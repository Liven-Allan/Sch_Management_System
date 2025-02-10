from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from . import forms, models
from django.db.models import Sum
from django.contrib import messages
from datetime import datetime
import zipfile
from django.utils.timezone import now
from io import BytesIO
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from .models import Subject, Class, Exam, Test, Configuration
from .forms import ExamForm, TestForm
from student.models import AcademicYear, Enrollment, Payment, Student, StudentFee, Term
from teacher.models import Teacher, Marks
from collections import OrderedDict, defaultdict
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from django.template.loader import get_template
from xhtml2pdf import pisa
import random
import string


from django.contrib.auth.models import User


# Home view (when the user is not authenticated)
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request, 'quiz/index.html')

# Check if the user is a teacher
def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

# Check if the user is a student
def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

# Redirect after login based on user role
def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')  # Student dashboard
    elif is_teacher(request.user):
        accountapproval = TMODEL.Teacher.objects.all().filter(user_id=request.user.id, status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')  # Teacher dashboard
        else:
            return render(request, 'teacher/teacher_wait_for_approval.html')  # Wait for approval
    else:
        return redirect('admin-dashboard')  # Admin dashboard

# Admin login redirection
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


# Admin dashboard view - includes stats like total students, teachers, courses, questions
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict = {
        'total_student': SMODEL.Student.objects.all().count(),  # Total students
        'total_teacher': TMODEL.Teacher.objects.all().filter(status=True).count(),  # Active teachers
        'total_course': models.Course.objects.all().count(),  # Total courses
        'total_question': models.Question.objects.all().count(),  # Total questions
    }
    return render(request, 'quiz/admin_dashboard.html', context=dict)

# Admin classes view - renders a page to add a class
@login_required(login_url='adminlogin')
def admin_classes_view(request):
    return render(request, 'quiz/admin_classes.html', {'message': 'Add Class'})

# TEACHER MANAGEMENT
# Admin view for teachers - including pending and approved teachers
#@login_required(login_url='adminlogin')
#def admin_teacher_view(request):
#    dict = {
#        'total_teacher': TMODEL.Teacher.objects.all().filter(status=True).count(),  # Total approved teachers
#        'pending_teacher': TMODEL.Teacher.objects.all().filter(status=False).count(),  # Pending teachers
#        'salary': TMODEL.Teacher.objects.all().filter(status=True).aggregate(Sum('salary'))['salary__sum'],  # Total salary
#    }
#    return render(request, 'quiz/admin_teacher.html', context=dict)
# Admin view for teachers - default view changed to admin_view_teacher.html
@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    # Fetch all approved teachers
    teachers = Teacher.objects.filter(status=True)

    # Fetch all classes in their natural order
    classes = Class.objects.all().order_by('id')  # Or any field that defines the natural order

    # Group teachers by class while preserving class order
    teachers_by_class = OrderedDict()
    for class_obj in classes:
        class_name = class_obj.class_name
        teachers_by_class[class_name] = []  # Initialize with empty list

    # Populate the grouped teachers
    for teacher in teachers:
        for assigned_class in teacher.assigned_classes.all():
            class_name = assigned_class.class_name
            if class_name in teachers_by_class:
                teachers_by_class[class_name].append(teacher)

    # Pass grouped teachers to the template
    return render(request, 'quiz/admin_view_teacher.html', {'teachers_by_class': teachers_by_class})

# Admin view for all approved teachers
@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=True)
    return render(request, 'quiz/admin_view_teacher.html', {'teachers': teachers})

# Update teacher details
@login_required(login_url='adminlogin')
def update_teacher_view(request, pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    user = TMODEL.User.objects.get(id=teacher.user_id)
    userForm = TFORM.TeacherUserForm(instance=user)
    teacherForm = TFORM.TeacherForm(request.FILES, instance=teacher)
    mydict = {'userForm': userForm, 'teacherForm': teacherForm}
    if request.method == 'POST':
        userForm = TFORM.TeacherUserForm(request.POST, instance=user)
        teacherForm = TFORM.TeacherForm(request.POST, request.FILES, instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request, 'quiz/update_teacher.html', context=mydict)


# Admin view for pending teachers (teachers awaiting approval)
@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=False)
    return render(request, 'quiz/admin_view_pending_teacher.html', {'teachers': teachers})

# Approve teacher (Admin)
@login_required(login_url='adminlogin')
def approve_teacher_view(request, pk):
    teacherSalary = forms.TeacherSalaryForm()
    if request.method == 'POST':
        teacherSalary = forms.TeacherSalaryForm(request.POST)
        if teacherSalary.is_valid():
            teacher = TMODEL.Teacher.objects.get(id=pk)
            teacher.salary = teacherSalary.cleaned_data['salary']
            teacher.status = True
            teacher.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-pending-teacher')
    return render(request, 'quiz/salary_form.html', {'teacherSalary': teacherSalary})

# Reject teacher (Admin)
@login_required(login_url='adminlogin')
def reject_teacher_view(request, pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    user = User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-pending-teacher')

# Admin view for teacher salary
@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=True)
    return render(request, 'quiz/admin_view_teacher_salary.html', {'teachers': teachers})

# Register teacher and immediately display grouped teacher records
@login_required(login_url='adminlogin')
def register_teacher_view(request):
    # Capture class_index from the URL
    class_index = request.GET.get('class_index', 0)

    userForm = TFORM.TeacherUserForm()
    teacherForm = TFORM.TeacherForm()

    if request.method == 'POST':
        userForm = TFORM.TeacherUserForm(request.POST)
        teacherForm = TFORM.TeacherForm(request.POST, request.FILES)

        if userForm.is_valid() and teacherForm.is_valid():
            # Create new user
            user = userForm.save()
            user.set_password(user.password)  # Encrypt the password
            user.save()
            
            # Create new teacher
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.status = True  # Automatically approve or set False for pending approval
            teacher.save()
            
            # Assign selected classes to the teacher
            teacher.assigned_classes.set(teacherForm.cleaned_data['assigned_classes'])

            # Fetch all approved teachers and group them by class
            teachers = Teacher.objects.filter(status=True)
            teachers_by_class = {}
            for teacher in teachers:
                for assigned_class in teacher.assigned_classes.all():
                    if assigned_class.class_name not in teachers_by_class:
                        teachers_by_class[assigned_class.class_name] = []
                    teachers_by_class[assigned_class.class_name].append(teacher)

            # Redirect back to the teachers' page with the same class_index
            return redirect(f"{reverse('admin-teachers')}?class_index={class_index}")

    # Render the teacher registration form
    return render(request, 'quiz/admin_teacher_signup.html', {
        'userForm': userForm,
        'teacherForm': teacherForm,
        'class_index': class_index,  # Pass class_index to the template
    })


# STUDENTS MANAGEMENT
# Admin view for all students

@login_required(login_url='adminlogin')
def admin_student_view(request):
    students = Student.objects.all().order_by('user__first_name')
    classes = Class.objects.all().order_by('id')

    students_by_class = OrderedDict()
    for class_obj in classes:
        class_name = class_obj.class_name
        students_by_class[class_name] = []  

    for student in students:
        if student.assigned_class:
            class_name = student.assigned_class.class_name
            if class_name in students_by_class:
                students_by_class[class_name].append(student)

    # Get the selected class from URL params
    selected_class = request.GET.get('class_name', '')

    return render(request, 'quiz/admin_view_student.html', {
        'students_by_class': students_by_class,
        'selected_class': selected_class
    })

# view students
@login_required(login_url='adminlogin')
def admin_students_view(request):
    students = Student.objects.select_related('assigned_class', 'user').order_by('user__first_name')
    classes = Class.objects.all().order_by('id')

    # Group students by class
    students_by_class = OrderedDict()
    for class_obj in classes:
        students_by_class[class_obj.class_name] = []

    for student in students:
        if student.assigned_class:
            class_name = student.assigned_class.class_name
            students_by_class[class_name].append(student)

    class_list = list(students_by_class.keys())  # Get class names in order
    total_classes = len(class_list)

    # Get class index from request, default to first class
    class_index = int(request.GET.get('class_index', 0))
    class_index = max(0, min(class_index, total_classes - 1)) if total_classes > 0 else 0

    # Get the currently selected class
    selected_class = class_list[class_index] if total_classes > 0 else None
    students_in_class = students_by_class.get(selected_class, [])

    return render(request, 'quiz/admin_students.html', {
        'students_in_class': students_in_class,
        'selected_class': selected_class,
        'class_index': class_index,
        'total_classes': total_classes,
    })

# delete student
@login_required(login_url='adminlogin')
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    class_index = request.GET.get('class_index', 0)  # Capture class index from request

    student.delete()
    messages.success(request, "Student deleted successfully.")

    return redirect(f"{reverse('admin-students')}?class_index={class_index}")

# teacher's view
@login_required(login_url='adminlogin')
def admin_teachers_view(request):
    teachers = Teacher.objects.select_related('user').order_by('user__first_name')
    classes = Class.objects.all().order_by('id')

    # Group teachers by class
    teachers_by_class = OrderedDict()
    for class_obj in classes:
        teachers_by_class[class_obj.class_name] = []

    for teacher in teachers:
        if teacher.assigned_classes.exists():
            for class_obj in teacher.assigned_classes.all():
                class_name = class_obj.class_name
                teachers_by_class[class_name].append(teacher)

    class_list = list(teachers_by_class.keys())  # Get class names in order
    total_classes = len(class_list)

    # Get class index from request, default to first class
    class_index = int(request.GET.get('class_index', 0))
    class_index = max(0, min(class_index, total_classes - 1)) if total_classes > 0 else 0

    # Get the currently selected class
    selected_class = class_list[class_index] if total_classes > 0 else None
    teachers_in_class = teachers_by_class.get(selected_class, [])

    return render(request, 'quiz/admin_teachers.html', {
        'teachers_in_class': teachers_in_class,
        'selected_class': selected_class,
        'class_index': class_index,
        'total_classes': total_classes,
    })

# delete teacher
# views.py
@login_required(login_url='adminlogin')
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    class_index = request.GET.get('class_index', 0)  # Capture class index from request

    teacher.delete()
    messages.success(request, "Teacher deleted successfully.")

    return redirect(f"{reverse('admin-teachers')}?class_index={class_index}")


@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students = SMODEL.Student.objects.all()
    return render(request, 'quiz/admin_view_student.html', {'students': students})

# Update student details (Admin)
@login_required(login_url='adminlogin')
def update_student_view(request, pk):
    student = SMODEL.Student.objects.get(id=pk)
    user = SMODEL.User.objects.get(id=student.user_id)
    userForm = SFORM.StudentUserForm(instance=user)
    studentForm = SFORM.StudentForm(request.FILES, instance=student)
    
    # Debug: Check if mobile and address are populated correctly
    print(f"Mobile: {studentForm.instance.mobile}")  # Check the mobile value
    print(f"Address: {studentForm.instance.address}")  # Check the address value
    
    mydict = {'userForm': userForm, 'studentForm': studentForm}
    
    if request.method == 'POST':
        userForm = SFORM.StudentUserForm(request.POST, instance=user)
        studentForm = SFORM.StudentForm(request.POST, request.FILES, instance=student)
        
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)  # Don't reset password if unchanged
            user.save()
            studentForm.save()  # Save student data including mobile and address
            return redirect('admin-view-student')
    
    return render(request, 'quiz/update_student.html', context=mydict)

# Register student
@login_required(login_url='adminlogin')
def register_student_view(request):
    class_index = request.GET.get('class_index', 0)  # Capture class index from URL

    if request.method == 'POST':
        userForm = SFORM.StudentUserForm(request.POST)
        studentForm = SFORM.StudentForm(request.POST, request.FILES)
        
        if userForm.is_valid() and studentForm.is_valid():
            first_name = userForm.cleaned_data['first_name']
            last_name = userForm.cleaned_data['last_name']
            random_number = ''.join(random.choices(string.digits, k=4))
            username = f"{first_name.lower()}{last_name.lower()}{random_number}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            student = studentForm.save(commit=False)
            student.user = user

            if not student.assigned_class:
                primary_1 = Class.objects.filter(class_name="Primary 1").first()
                if primary_1:
                    student.assigned_class = primary_1

            student.save()
            student.assigned_subjects.set(studentForm.cleaned_data['assigned_subjects'])
            student.save()

            # Redirect back to admin-students with the same class_index
            return redirect(f"{reverse('admin-students')}?class_index={class_index}")

    else:
        userForm = SFORM.StudentUserForm()
        studentForm = SFORM.StudentForm()

    return render(request, 'quiz/admin_student_signup.html', {
        'userForm': userForm,
        'studentForm': studentForm,
        'class_index': class_index,
    })


# academic year
@login_required(login_url='adminlogin')
def manage_academic_years_view(request):
    if request.method == 'POST':
        year_form = SFORM.AcademicYearForm(request.POST)
        terms = request.POST.getlist('terms')
        if year_form.is_valid():
            academic_year = year_form.save()
            for term_name in terms:
                if term_name.strip():  # Avoid empty term names
                    Term.objects.create(academic_year=academic_year, term_name=term_name.strip())
            return redirect('manage_academic_years')
    else:
        year_form = SFORM.AcademicYearForm()
    years = AcademicYear.objects.prefetch_related('terms').all()
    return render(request, 'quiz/manage_academic_years.html', {'year_form': year_form, 'years': years})

# delete year
@login_required(login_url='adminlogin')
def delete_academic_year_view(request, year_id):
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    academic_year.delete()
    messages.success(request, 'Academic year deleted successfully.')
    return redirect('manage_academic_years')

# delete term
@login_required(login_url='adminlogin')
def delete_term_view(request, term_id):
    term = get_object_or_404(Term, id=term_id)
    term.delete()
    messages.success(request, 'Term deleted successfully.')
    return redirect('manage_academic_years')

# academic term
@login_required(login_url='adminlogin')
def manage_terms_view(request, year_id):
    year = get_object_or_404(AcademicYear, id=year_id)
    if request.method == 'POST':
        form = SFORM.TermForm(request.POST)
        if form.is_valid():
            term = form.save(commit=False)
            term.academic_year = year
            term.save()
            return redirect('manage_terms', year_id=year.id)
    else:
        form = SFORM.TermForm()
    terms = year.terms.all()
    return render(request, 'quiz/manage_terms.html', {'form': form, 'terms': terms, 'year': year})

# enroll students
@login_required(login_url='adminlogin')
def enroll_students_view(request, year_id, term_id):
    year = get_object_or_404(AcademicYear, id=year_id)
    term = get_object_or_404(Term, id=term_id)
    assigned_classes = Class.objects.all()
    enrollments_by_class = defaultdict(list)

    enrollments = Enrollment.objects.filter(
        academic_year=year,
        term=term
    ).select_related('assigned_class', 'student__user')

    for enrollment in enrollments:
        class_name = enrollment.assigned_class.class_name
        enrollments_by_class[class_name].append(enrollment)

    if request.method == 'POST':
        form = SFORM.EnrollmentForm(request.POST)
        if form.is_valid():
            assigned_class = form.cleaned_data.get('assigned_class')
            students = form.cleaned_data.get('students')

            for student in students:
                if Enrollment.objects.filter(
                    student=student,
                    academic_year=year,
                    term=term,
                    assigned_class=assigned_class
                ).exists():
                    messages.warning(request, f'{student.user.get_full_name()} is already enrolled in this class for this term!')
                else:
                    # Create the Enrollment
                    enrollment = Enrollment.objects.create(
                        student=student,
                        academic_year=year,
                        term=term,
                        assigned_class=assigned_class
                    )

                    # After Enrollment is created, capture the student fee
                    class_fee_key = f"{assigned_class.class_name.lower().replace(' ', '_')}_fee"
                    class_fee_config = Configuration.objects.filter(key=class_fee_key).first()
                    total_fee = float(class_fee_config.value) if class_fee_config else 0.0

                    # Create or update the StudentFee record for this enrollment
                    StudentFee.objects.create(
                        student=student,
                        academic_year=year,
                        term=term,
                        assigned_class=assigned_class,
                        total_fee=total_fee,
                        balance=total_fee  # Assuming no payments have been made at this point
                    )

                    messages.success(request, f'{student.user.get_full_name()} enrolled successfully!')

            return redirect('enroll_students', year_id=year.id, term_id=term.id)
    else:
        form = SFORM.EnrollmentForm()

    return render(request, 'quiz/enroll_students.html', {
        'form': form,
        'assigned_classes': assigned_classes,
        'year': year,
        'term': term,
        'enrollments_by_class': enrollments_by_class
    })



# enrolled students
@login_required(login_url='adminlogin')
def get_enrollments_view(request, year_id, term_id):
    """
    Retrieve enrollment records grouped by assigned class for a specific year and term.
    Ensure that classes are ordered from Primary 1 to Primary 7.
    """
    year = get_object_or_404(AcademicYear, id=year_id)
    term = get_object_or_404(Term, id=term_id)

    # Define the fixed order of classes
    class_order = [
        'Primary 1', 'Primary 2', 'Primary 3', 'Primary 4', 
        'Primary 5', 'Primary 6', 'Primary 7'
    ]

    enrollments_by_class = defaultdict(list)
    enrollments = Enrollment.objects.filter(
        academic_year=year,
        term=term
    ).select_related('assigned_class', 'student__user')

    for enrollment in enrollments:
        class_name = enrollment.assigned_class.class_name
        enrollments_by_class[class_name].append({
            "student_name": enrollment.student.user.get_full_name(),
            "enrollment_id": enrollment.id
        })

    # Order the classes according to the predefined class_order list
    ordered_enrollments_by_class = {class_name: enrollments_by_class[class_name] 
                                    for class_name in class_order if class_name in enrollments_by_class}

    # Alphabetically sort students in each class
    for class_name, students in ordered_enrollments_by_class.items():
        ordered_enrollments_by_class[class_name] = sorted(students, key=lambda x: x['student_name'])

    return JsonResponse({"enrollments_by_class": ordered_enrollments_by_class})

# unenroll
@login_required(login_url='adminlogin')
def unenroll_student(request, enrollment_id):
    """
    Unenroll a student by deleting the Enrollment record and associated StudentFee record.
    """
    # Get the enrollment object by its ID
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # Delete the corresponding StudentFee record
    StudentFee.objects.filter(
        student=enrollment.student,
        academic_year=enrollment.academic_year,
        term=enrollment.term,
        assigned_class=enrollment.assigned_class
    ).delete()

    # Delete the enrollment
    enrollment.delete()

    # Redirect back to the page showing enrollments
    return redirect('enroll_students', year_id=enrollment.academic_year.id, term_id=enrollment.term.id)


# get students by class
@login_required(login_url='adminlogin')
def get_students_by_class(request, class_id):
    students = Student.objects.filter(assigned_class_id=class_id).values('id', 'user__first_name', 'user__last_name')
    student_list = [{'id': student['id'], 'name': f"{student['user__first_name']} {student['user__last_name']}"} for student in students]
    return JsonResponse({'students': student_list})

# Fees payment view
@login_required(login_url='adminlogin')
def manage_payment_view(request, student_id):
    student_fee = get_object_or_404(StudentFee, student__id=student_id)

    if request.method == 'POST':
        try:
            payment_amount = Decimal(request.POST.get('payment_amount', '0.0'))
        except InvalidOperation:
            messages.error(request, "Invalid payment amount entered.")
            return redirect(request.path_info)

        if payment_amount <= 0:
            messages.error(request, "Payment amount must be greater than zero.")
            return redirect(request.path_info)

        if payment_amount > student_fee.balance:
            messages.error(
                request,
                f"Payment amount cannot exceed the remaining balance of {student_fee.balance:.2f}."
            )
            return redirect(request.path_info)

        payment_date = request.POST.get('payment_date')

        payment = Payment(
            student_fee=student_fee,
            payment_amount=payment_amount,
            payment_date=payment_date
        )
        payment.save()

        student_fee.save()  # Update balance
        
        messages.success(request, f"Payment of {payment_amount:.2f} recorded successfully!")

        # Preserve class_index, year_id, and term_id
        return redirect(f"{reverse('student-fees')}?year_id={request.GET.get('year_id')}&term_id={request.GET.get('term_id')}&class_index={request.GET.get('class_index')}")

    return render(request, 'quiz/manage_payment.html', {'student_fee': student_fee})

# student fees view
@login_required(login_url='adminlogin')
def student_fees_view(request):
    latest_year = AcademicYear.objects.all().order_by('-year_name').first()
    first_term = Term.objects.filter(academic_year=latest_year).order_by('id').first() if latest_year else None

    year_id = request.GET.get('year_id', latest_year.id if latest_year else None)
    term_id = request.GET.get('term_id', first_term.id if first_term else None)
    class_index = request.GET.get('class_index', '0')  # Get value, default to '0'
    class_index = int(class_index) if class_index.isdigit() else 0  # Convert only if valid


    years = AcademicYear.objects.all()
    terms = Term.objects.filter(academic_year_id=year_id) if year_id else Term.objects.none()

    student_fees = StudentFee.objects.select_related('assigned_class', 'student', 'academic_year', 'term')
    
    if year_id and term_id:
       enrolled_students = Enrollment.objects.filter(
          academic_year_id=year_id,
          term_id=term_id
        ).values_list('student', flat=True)
    student_fees = student_fees.filter(student__in=enrolled_students)

    # Ensure students are ordered alphabetically by first name and then last name
    student_fees = student_fees.order_by('student__user__first_name', 'student__user__last_name')


    # Group fees by class
    fees_by_class = {}
    for fee in student_fees:
        last_payment = fee.payments.order_by('-payment_date').first()
        fee.last_payment_date = last_payment.payment_date if last_payment else None
        fee.amount_paid = sum(payment.payment_amount for payment in fee.payments.all())
        class_name = fee.assigned_class.class_name if fee.assigned_class else "Unassigned"
        fees_by_class.setdefault(class_name, []).append(fee)

    class_list = sorted(fees_by_class.keys())  # Sort classes alphabetically
    total_classes = len(class_list)

    # Ensure class_index is within bounds
    class_index = max(0, min(class_index, total_classes - 1)) if total_classes > 0 else 0
    current_class = class_list[class_index] if total_classes > 0 else None
    current_fees = fees_by_class.get(current_class, [])

    selected_year_name = AcademicYear.objects.filter(id=year_id).first().year_name if year_id else (latest_year.year_name if latest_year else None)
    selected_term_name = Term.objects.filter(id=term_id).first().term_name if term_id else (first_term.term_name if first_term else None)

    return render(request, 'quiz/admin_student_fees.html', {
        'current_class': current_class,
        'current_fees': current_fees,
        'class_index': class_index,
        'total_classes': total_classes,
        'years': years,
        'terms': terms,
        'selected_year': year_id,
        'selected_term': term_id,
        'selected_year_name': selected_year_name,
        'selected_term_name': selected_term_name,
    })


# fees records
@login_required(login_url='adminlogin')
def fees_records_view(request):
    # Get the latest academic year and term
    latest_year = AcademicYear.objects.order_by('-year_name').first()
    first_term = Term.objects.filter(academic_year=latest_year).order_by('id').first() if latest_year else None

    # Selected year and term from GET parameters or defaults
    year_id = request.GET.get('year_id', latest_year.id if latest_year else None)
    term_id = request.GET.get('term_id', first_term.id if first_term else None)

    # Fetch years and terms for the dropdowns
    years = AcademicYear.objects.all()
    terms = Term.objects.filter(academic_year_id=year_id) if year_id else Term.objects.none()

    # Query to fetch class-based fees records
    fees_data = []
    if year_id and term_id:
        classes = Class.objects.all()
        for class_obj in classes:
            # Students in the class for the selected year and term
            students_in_class = Enrollment.objects.filter(
                assigned_class=class_obj,
                academic_year_id=year_id,
                term_id=term_id
            )

            # Calculate totals
            total_students = students_in_class.count()
            total_fees = StudentFee.objects.filter(
                student__in=students_in_class.values_list('student', flat=True)
            ).aggregate(total=Sum('total_fee'))['total'] or 0
            total_balance = StudentFee.objects.filter(
                student__in=students_in_class.values_list('student', flat=True)
            ).aggregate(balance=Sum('balance'))['balance'] or 0

            fees_data.append({
                'class_name': class_obj.class_name,
                'total_students': total_students,
                'total_fees': total_fees,
                'fees_balance': total_balance,
            })

    return render(request, 'quiz/admin_fees_records.html', {
        'fees_data': fees_data,
        'years': years,
        'terms': terms,
        'selected_year': year_id,
        'selected_term': term_id,
        'selected_year_name': latest_year.year_name if latest_year else None,
        'selected_term_name': first_term.term_name if first_term else None,
    })

# generate fees summary
@login_required(login_url='adminlogin')
def generate_summary_pdf(request):
    year_id = request.GET.get('year')
    term_id = request.GET.get('term')

    # Fetch selected year and term
    year = AcademicYear.objects.filter(id=year_id).first()
    term = Term.objects.filter(id=term_id).first()

    # Calculate total students and total fees
    total_students = Enrollment.objects.filter(
        academic_year_id=year_id, term_id=term_id
    ).count()

    total_fees = StudentFee.objects.filter(
        student__enrollment__academic_year_id=year_id,
        student__enrollment__term_id=term_id
    ).aggregate(total=Sum('total_fee'))['total'] or 0

    # Get current date
    current_date = now().strftime('%Y-%m-%d')

    summary_data = {
        'selected_year': year.year_name if year else "N/A",
        'selected_term': term.term_name if term else "N/A",
        'total_students': total_students,
        'total_fees': total_fees,
        'today': current_date,  # Add this to the template data
    }

    # Render PDF
    template = get_template('quiz/fees_summary_pdf.html')
    html = template.render(summary_data)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fees_summary.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had errors <pre>' + html + '</pre>')

    return response

# student balance
@login_required(login_url='adminlogin')
def fetch_balances(request):
    class_name = request.GET.get('class_name')
    year_id = request.GET.get('year_id')
    term_id = request.GET.get('term_id')
    class_index = request.GET.get('class_index')

    if class_name:
        students = Enrollment.objects.filter(assigned_class__class_name=class_name)
        student_balances = StudentFee.objects.filter(student__in=students.values_list('student', flat=True))

        balances_data = [
            {
                'student_name': f"{student_fee.student.user.first_name} {student_fee.student.user.last_name}",
                'balance': student_fee.balance,
            }
            for student_fee in student_balances
        ]

        return render(
            request,
            'quiz/balances.html',
            {
                'balances_data': balances_data,
                'class_name': class_name,
                'year_id': year_id,
                'term_id': term_id,
                'class_index': class_index,
            }
        )

    return redirect('fees_records')  # Redirect if class_name is not provided


# print pdf file
@login_required(login_url='adminlogin')
def generate_balances_pdf(request):
    class_name = request.GET.get('class_name')

    if not class_name:
        return HttpResponse("Class name is required", status=400)

    students = Enrollment.objects.filter(assigned_class__class_name=class_name)
    student_balances = StudentFee.objects.filter(student__in=students.values_list('student', flat=True))

    # Get the current date and time
    current_date = now().strftime('%Y-%m-%d')

    # Render HTML Template (Using balances_pdf.html)
    html_string = render_to_string('quiz/balances_pdf.html', {
        'class_name': class_name,
        'student_balances': student_balances,
        'current_date': current_date,  # Add date to the template
    })

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="balances_{class_name}.pdf"'
    HTML(string=html_string).write_pdf(response)

    return response

# view payments
@login_required(login_url='adminlogin')
def view_payments_view(request, student_id):
    # Get the student's fee record
    student_fee = get_object_or_404(StudentFee, student_id=student_id)

    # Get all payments made by the student
    payments = Payment.objects.filter(student_fee=student_fee).order_by('-payment_date')

    return render(request, 'quiz/view_payments.html', {'student_fee': student_fee, 'payments': payments})

# editing payment
@login_required(login_url='adminlogin')
def edit_payment_view(request, payment_id):
    # Get the payment record
    payment = get_object_or_404(Payment, id=payment_id)
    student_fee = payment.student_fee
    
    if request.method == 'POST':
        form = SFORM.PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            # Save the updated payment details
            form.save()

            # Recalculate the balance for the student fee
            student_fee.save()  # This will update the balance field
            
            return redirect('view_payments', student_id=student_fee.student.id)
    else:
        form = SFORM.PaymentForm(instance=payment)

    return render(request, 'quiz/edit_payment.html', {'form': form, 'payment': payment})

# CLASS MANAGEMENT
@login_required(login_url='adminlogin')
def admin_classes_view(request):
    classes = models.Class.objects.all()  # Get all classes
    return render(request, 'quiz/admin_view_classes.html', {'classes': classes})

@login_required(login_url='adminlogin')
def add_class_view(request):
    if request.method == 'POST':
        form = forms.ClassForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new class
            return redirect('admin-classes')  # Redirect to the class list view
    else:
        form = forms.ClassForm()
    return render(request, 'quiz/add_class.html', {'form': form})

# Delete class (Admin)
@login_required(login_url='adminlogin')
def delete_class_view(request, id):
    # Get the class object by ID
    class_to_delete = models.Class.objects.get(id=id)
    
    # Delete the class object
    class_to_delete.delete()

    # Redirect back to the class list view after deletion
    return HttpResponseRedirect('/admin-classes') 

# add subject
@login_required(login_url='adminlogin')
def add_subject_view(request, class_id):
    class_instance = models.Class.objects.get(id=class_id)
    if request.method == 'POST':
        form = forms.SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-classes')
    else:
        form = forms.SubjectForm(initial={'class_name': class_instance})
    return render(request, 'quiz/add_subject.html', {'form': form, 'class_name': class_instance.class_name})

# get subject by class
def get_subjects_by_class(request):
    class_id = request.GET.get('class_id')
    subjects = Subject.objects.filter(class_name_id=class_id).values('id', 'subject_name')
    return JsonResponse(list(subjects), safe=False)

# EXAMS AND TEST MANAGEMENT
@login_required(login_url='adminlogin')
def assessments_view(request):
    exams = Exam.objects.all().order_by('-id')
    tests = Test.objects.all().order_by('-id')
    return render(request, 'quiz/assessments.html', {'exams': exams, 'tests': tests})


@login_required(login_url='adminlogin')
def add_exam_view(request):
    form = ExamForm()
    context = {
        'form': form,
        'model_name': form._meta.model.__name__,  # Get the model name from the form's Meta class
    }
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assessments')  # Adjust the redirect URL as needed
    return render(request, 'quiz/add_exam.html', context)

@login_required(login_url='adminlogin')
def add_test_view(request):
    form = TestForm()
    context = {
        'form': form,
        'model_name': form._meta.model.__name__,  # Get the model name from the form's Meta class
    }
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assessments')  # Adjust the redirect URL as needed
    return render(request, 'quiz/add_test.html', context)

# Edit Exam view
@login_required(login_url='adminlogin')
def edit_exam_view(request, id):
    exam = get_object_or_404(Exam, id=id)
    form = ExamForm(instance=exam)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect('assessments')
    return render(request, 'quiz/add_exam.html', {'form': form, 'model_name': 'Exam'})

# Edit Test view
@login_required(login_url='adminlogin')
def edit_test_view(request, id):
    test = get_object_or_404(Test, id=id)
    form = TestForm(instance=test)
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            return redirect('assessments')
    return render(request, 'quiz/add_test.html', {'form': form, 'model_name': 'Test'})

# Delete Exam view
@login_required(login_url='adminlogin')
def delete_exam_view(request, id):
    exam = get_object_or_404(Exam, id=id)
    exam.delete()
    return redirect('assessments')

# Delete Test view
@login_required(login_url='adminlogin')
def delete_test_view(request, id):
    test = get_object_or_404(Test, id=id)
    test.delete()
    return redirect('assessments')

# Results Management
# exam view
# views.py
@login_required(login_url='adminlogin')
def exam_results_view(request):
    # Fetch all classes in their natural order
    classes = Class.objects.all().order_by('id')  # Or any field that defines the natural order

    # Create an ordered dictionary to group students by their assigned class
    marked_students_by_class = OrderedDict()
    for class_obj in classes:
        class_name = class_obj.class_name
        marked_students_by_class[class_name] = []  # Initialize with empty list

    # Fetch all marks with their associated student and exam
    marks = Marks.objects.select_related('student', 'exam').filter(exam__isnull=False)

    # Populate the grouped students, ensuring alphabetical order within each class
    for mark in marks:
        student = mark.student
        student_class = student.assigned_class.class_name if student.assigned_class else "Unassigned"

        if student_class in marked_students_by_class:
            subject_marks_dict = {}
            for item in mark.subject_marks:
                try:
                    subject_id = int(item['subject_id'])
                    marks = int(item['marks'])
                    subject_name = Subject.objects.get(id=subject_id).subject_name
                    subject_marks_dict[subject_name] = marks
                except ValueError:
                    subject_marks_dict["Unknown"] = None

            marked_students_by_class[student_class].append({
                'name': student.get_name,
                'profile_pic': student.profile_pic.url if student.profile_pic else None,
                'exam': str(mark.exam) if mark.exam else "N/A",
                'subject_marks': subject_marks_dict,
                'mark': mark
            })

    # Sort students alphabetically by their name within each class
    for class_name, students in marked_students_by_class.items():
        marked_students_by_class[class_name] = sorted(students, key=lambda x: x['name'].lower())

    # Get the selected class from the URL query parameters (if provided)
    selected_class = request.GET.get('selected_class', None)

    context = {
        'marked_students_by_class': marked_students_by_class,
        'selected_class': selected_class,  # Pass the selected class to the template
    }
    return render(request, 'quiz/exam_results.html', context)

# admin view exams
@login_required(login_url='adminlogin')
def admin_edit_exam_marks_view(request, mark_id):
    mark = get_object_or_404(Marks, id=mark_id)
    student = mark.student
    class_name = student.assigned_class.class_name if hasattr(student, 'assigned_class') and student.assigned_class else "Unassigned"
     # Fetch the school pay code
    school_pay_code = Configuration.objects.filter(key='school_pay_code').first().value if Configuration.objects.filter(key='school_pay_code').exists() else 'Not Set'
    # Allowed classes for showing the Major 4 Total
    allowed_classes = ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]

    # Add the condition to check if the class is in the allowed list
    show_agg_column = class_name in allowed_classes

    # Fetch marks for all students in the same class
    class_marks = Marks.objects.filter(student__assigned_class=student.assigned_class, exam__isnull=False)
    
    # Debugging output moved after the variables are assigned
    print(f"Debug: class_name = {class_name}, show_agg_column = {show_agg_column}")  # Debug statement
    print(f"Debug: class_marks count = {class_marks.count()}")  # Debug statement

    is_primary_4_7 = class_name in ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]

    student_password = student.user.password
    student_lin = student.learner_lin

    subject_abbreviations = {
        "MATHEMATICS": "MATHS",
        "ENGLISH": "ENGLISH",
        "LITERACY 1": "LITERACY 1",
        "RELIGIOUS EDUCATION": "R.E",
        "READING": "READING",
        "LUGANDA": "LUGANDA",
        "WRITING (LIT ll)": "WRITING (LIT 11)",
        "SCIENCE": "SCIENCE",
        "SOCIAL STUDIES": "SOCIAL STUDIES",
    }

    exam_records = []

    for class_mark in class_marks:
        subject_marks = class_mark.subject_marks or []
        exam = class_mark.exam
        exam_name = f"{exam.year} - {exam.term}" if exam else "N/A"

        exam_record = {
            'student_name': f"{class_mark.student.user.first_name} {class_mark.student.user.last_name}",
            'exam_name': exam_name,
            'year': exam.year if exam else None,
            'term': exam.term if exam else None,
            'subject_marks': [],
            'total_marks': 0,
            'total_full_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0
        total_full_marks = 0
        subject_aggregates = []

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                remarks = calculate_remarks(marks)

                total_marks += marks
                total_full_marks += 100
                aggregate = calculate_aggregate(marks)
                total_aggregate += aggregate

                exam_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'remarks': remarks,
                    'aggregate': aggregate,
                })

        exam_record['total_marks'] = total_marks
        exam_record['total_full_marks'] = total_full_marks
        exam_record['total_aggregate'] = total_aggregate
        exam_record['div'] = calculate_division(total_aggregate)
        exam_records.append(exam_record)

    exam_records = sorted(exam_records, key=lambda x: x['total_marks'], reverse=True)

    # Fetch test records for the same student
    test_marks = Marks.objects.filter(student=student, test__isnull=False)
    print(f"Debug: test_marks count = {test_marks.count()}")  # Debug statement

    # Fetch the class of the current student
    student_class = student.assigned_class if hasattr(student, 'assigned_class') else None
    # Fetch marks for all students in the same class for relevant tests
    all_class_marks = Marks.objects.filter(student__assigned_class=student_class, test__isnull=False)


    # Define subject abbreviations
    subject_abbreviations = {
        "MATHEMATICS": "MTC",
        "ENGLISH": "ENG",
        "LITERACY 1": "LIT 1A",
        "RELIGIOUS EDUCATION": "C.R.E",
        "READING": "READ",
        "LUGANDA": "LUG",
        "WRITING (LIT ll)": "WRITING",
        "SCIENCE": "SCI",
        "SOCIAL STUDIES": "SST",
    }

    # Group test records by month and term
    test_records_by_month_term = defaultdict(list)

    for class_mark in all_class_marks:
        subject_marks = class_mark.subject_marks or []
        month = class_mark.test.month if class_mark.test else None
        term = class_mark.test.term if class_mark.test else None

        test_record = {
            'student': class_mark.student.get_name,
            'month': month,
            'term': term,
            'subject_marks': [],
            'total_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                aggregate = calculate_aggregate(marks)  # Compute aggregate for the subject
                
                total_marks += marks
                total_aggregate += aggregate

                test_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'aggregate': aggregate,  # Subject aggregate
                })

        test_record['total_marks'] = total_marks
        test_record['total_aggregate'] = total_aggregate  # Sum of all subject aggregates
        test_record['div'] = calculate_division(total_aggregate)  # Compute division based on total aggregate

        # Group by month and term
        test_records_by_month_term[(month, term)].append(test_record)

    # Assign positions within each month and term group
    for (month, term), records in test_records_by_month_term.items():
        # Sort by total marks (descending order)
        records.sort(key=lambda x: x['total_marks'], reverse=True)
        # Assign positions
        for idx, record in enumerate(records):
            record['position'] = idx + 1

    # Filter records for the current student
    student_test_records = [
        record for records in test_records_by_month_term.values() for record in records
        if record['student'] == student.get_name
    ]
   

    rank = 0
    previous_total = None
    current_position = None

    for exam_record in exam_records:
        rank += 1
        if exam_record['total_marks'] != previous_total:
            current_position = rank
        exam_record['position'] = current_position
        previous_total = exam_record['total_marks']

    student_records = [exam_record for exam_record in exam_records if exam_record['student_name'] == f"{student.user.first_name} {student.user.last_name}"]

    total_students = len(class_marks)
    current_date = datetime.now().strftime('%B %d, %Y')  # Format: January 09, 2025
    next_term_start = Configuration.objects.filter(key='next_term_start').first()
    next_term_end = Configuration.objects.filter(key='next_term_end').first()
    brooms_count = Configuration.objects.filter(key='brooms_count').first()
    toilet_paper_count = Configuration.objects.filter(key='toilet_paper_count').first()
    # Fetch the fees for each primary class
    primary_1_fee = Configuration.objects.filter(key='primary_1_fee').first()
    primary_2_fee = Configuration.objects.filter(key='primary_2_fee').first()
    primary_3_fee = Configuration.objects.filter(key='primary_3_fee').first()
    primary_4_fee = Configuration.objects.filter(key='primary_4_fee').first()
    primary_5_fee = Configuration.objects.filter(key='primary_5_fee').first()
    primary_6_fee = Configuration.objects.filter(key='primary_6_fee').first()
    primary_7_fee = Configuration.objects.filter(key='primary_7_fee').first()

    # Fetch the fee specific to the student's class
    fee_mapping = {
       "Primary 1": primary_1_fee.value if primary_1_fee else '0',
       "Primary 2": primary_2_fee.value if primary_2_fee else '0',
       "Primary 3": primary_3_fee.value if primary_3_fee else '0',
       "Primary 4": primary_4_fee.value if primary_4_fee else '0',
       "Primary 5": primary_5_fee.value if primary_5_fee else '0',
       "Primary 6": primary_6_fee.value if primary_6_fee else '0',
       "Primary 7": primary_7_fee.value if primary_7_fee else '0',
    }


        # Get the fee for the student's class
    student_fee = fee_mapping.get(class_name, 0)  # Default to 0 if class is not in the mapping
    # If student_fee is a string with a fee and key (like "primary_1_fee: 350000")
    if isinstance(student_fee, str) and ':' in student_fee:
       student_fee = student_fee.split(':')[1]  # Get only the numeric fee


    return render(request, 'quiz/admin_edit_exam_marks.html', {
        'mark': mark,
        'school_pay_code': school_pay_code,
        'exam_records': student_records,
        'test_records': student_test_records,
        'class_name': class_name,
        'is_primary_4_7': is_primary_4_7,
        'current_position': student_records[0]['position'] if student_records else None,
        'total_students': total_students,
        'show_agg_column': show_agg_column,  # Pass the condition to the template
        'allowed_classes': allowed_classes,  # Pass the allowed classes to the template
        'current_date': current_date,  # Add the current date to context
        'next_term_start': next_term_start.value if next_term_start else '',
        'next_term_end': next_term_end.value if next_term_end else '',
        'brooms_count': brooms_count.value if brooms_count else '0',
        'toilet_paper_count': toilet_paper_count.value if toilet_paper_count else '0',
        'student_fee': student_fee,
        'student_lin': student_lin,
    })

# exam pdf
@login_required(login_url='adminlogin')
def generate_exam_pdf(request, mark_id):
    mark = get_object_or_404(Marks, id=mark_id)
    student = mark.student
    class_name = student.assigned_class.class_name if hasattr(student, 'assigned_class') and student.assigned_class else "Unassigned"
    
    # Fetch the school pay code
    school_pay_code = Configuration.objects.filter(key='school_pay_code').first().value if Configuration.objects.filter(key='school_pay_code').exists() else 'Not Set'
    # Allowed classes for showing the Major 4 Total
    allowed_classes = ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]
    show_agg_column = class_name in allowed_classes

    # Fetch marks for all students in the same class
    class_marks = Marks.objects.filter(student__assigned_class=student.assigned_class, exam__isnull=False)
    
    exam_records = []

    for class_mark in class_marks:
        subject_marks = class_mark.subject_marks or []
        exam = class_mark.exam
        exam_name = f"{exam.year} - {exam.term}" if exam else "N/A"

        exam_record = {
            'student_name': f"{class_mark.student.user.first_name} {class_mark.student.user.last_name}",
            'exam_name': exam_name,
            'year': exam.year if exam else None,
            'term': exam.term if exam else None,
            'subject_marks': [],
            'total_marks': 0,
            'total_full_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0
        total_full_marks = 0

        is_primary_4_7 = class_name in ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]

        subject_abbreviations = {
           "MATHEMATICS": "MATHS",
           "ENGLISH": "ENGLISH",
           "LITERACY 1": "LITERACY 1",
           "RELIGIOUS EDUCATION": "R.E",
           "READING": "READING",
           "LUGANDA": "LUGANDA",
           "WRITING (LIT ll)": "WRITING (LIT 11)",
           "SCIENCE": "SCIENCE",
           "SOCIAL STUDIES": "SOCIAL STUDIES",
        }

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                remarks = calculate_remarks(marks)
                aggregate = calculate_aggregate(marks)

                total_marks += marks
                total_full_marks += 100  # Assuming full marks per subject is 100
                total_aggregate += aggregate

                exam_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'remarks': remarks,
                    'aggregate': aggregate,
                })

        exam_record['total_marks'] = total_marks
        exam_record['total_full_marks'] = total_full_marks
        exam_record['total_aggregate'] = total_aggregate
        exam_record['div'] = calculate_division(total_aggregate)
        exam_records.append(exam_record)

    # Fetch test records for the same student
    # Fetch the class of the current student
    student_class = student.assigned_class if hasattr(student, 'assigned_class') else None
    # Fetch marks for all students in the same class for relevant tests
    all_class_marks = Marks.objects.filter(student__assigned_class=student_class, test__isnull=False)


    # Define subject abbreviations
    subject_abbreviations = {
        "MATHEMATICS": "MTC",
        "ENGLISH": "ENG",
        "LITERACY 1": "LIT 1A",
        "RELIGIOUS EDUCATION": "C.R.E",
        "READING": "READ",
        "LUGANDA": "LUG",
        "WRITING (LIT ll)": "WRITING",
        "SCIENCE": "SCI",
        "SOCIAL STUDIES": "SST",
    }

    # Group test records by month and term
    test_records_by_month_term = defaultdict(list)

    for class_mark in all_class_marks:
        subject_marks = class_mark.subject_marks or []
        month = class_mark.test.month if class_mark.test else None
        term = class_mark.test.term if class_mark.test else None

        test_record = {
            'student': class_mark.student.get_name,
            'month': month,
            'term': term,
            'subject_marks': [],
            'total_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                aggregate = calculate_aggregate(marks)  # Compute aggregate for the subject
                
                total_marks += marks
                total_aggregate += aggregate

                test_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'aggregate': aggregate,  # Subject aggregate
                })

        test_record['total_marks'] = total_marks
        test_record['total_aggregate'] = total_aggregate  # Sum of all subject aggregates
        test_record['div'] = calculate_division(total_aggregate)  # Compute division based on total aggregate

        # Group by month and term
        test_records_by_month_term[(month, term)].append(test_record)

    # Assign positions within each month and term group
    for (month, term), records in test_records_by_month_term.items():
        # Sort by total marks (descending order)
        records.sort(key=lambda x: x['total_marks'], reverse=True)
        # Assign positions
        for idx, record in enumerate(records):
            record['position'] = idx + 1

    # Filter records for the current student
    student_test_records = [
        record for records in test_records_by_month_term.values() for record in records
        if record['student'] == student.get_name
    ]
   

    # Fetch configuration values for the student
    total_students = len(class_marks)
    student_fee = Configuration.objects.filter(key=f"{class_name.lower()}_fee").first().value if Configuration.objects.filter(key=f"{class_name.lower()}_fee").exists() else '0'
    student_lin = student.learner_lin
    current_date = datetime.now().strftime('%B %d, %Y')
    next_term_start = Configuration.objects.filter(key='next_term_start').first()
    next_term_end = Configuration.objects.filter(key='next_term_end').first()
    brooms_count = Configuration.objects.filter(key='brooms_count').first()
    toilet_paper_count = Configuration.objects.filter(key='toilet_paper_count').first()
     # Fetch the fees for each primary class
    primary_1_fee = Configuration.objects.filter(key='primary_1_fee').first()
    primary_2_fee = Configuration.objects.filter(key='primary_2_fee').first()
    primary_3_fee = Configuration.objects.filter(key='primary_3_fee').first()
    primary_4_fee = Configuration.objects.filter(key='primary_4_fee').first()
    primary_5_fee = Configuration.objects.filter(key='primary_5_fee').first()
    primary_6_fee = Configuration.objects.filter(key='primary_6_fee').first()
    primary_7_fee = Configuration.objects.filter(key='primary_7_fee').first()

    # Fetch the fee specific to the student's class
    fee_mapping = {
       "Primary 1": primary_1_fee.value if primary_1_fee else '0',
       "Primary 2": primary_2_fee.value if primary_2_fee else '0',
       "Primary 3": primary_3_fee.value if primary_3_fee else '0',
       "Primary 4": primary_4_fee.value if primary_4_fee else '0',
       "Primary 5": primary_5_fee.value if primary_5_fee else '0',
       "Primary 6": primary_6_fee.value if primary_6_fee else '0',
       "Primary 7": primary_7_fee.value if primary_7_fee else '0',
    }


        # Get the fee for the student's class
    student_fee = fee_mapping.get(class_name, 0)  # Default to 0 if class is not in the mapping
    # If student_fee is a string with a fee and key (like "primary_1_fee: 350000")
    if isinstance(student_fee, str) and ':' in student_fee:
       student_fee = student_fee.split(':')[1]  # Get only the numeric fee
    
    exam_records.sort(key=lambda x: x['total_marks'], reverse=True)

    rank = 0
    previous_total = None
    current_position = None

    for exam_record in exam_records:
        rank += 1
        if exam_record['total_marks'] != previous_total:
            current_position = rank
        exam_record['position'] = current_position
        previous_total = exam_record['total_marks']   

    student_records = [exam_record for exam_record in exam_records if exam_record['student_name'] == f"{student.user.first_name} {student.user.last_name}"]    

    student_name = mark.student.get_name 
    # Render the HTML template for the PDF
    context = {
        'mark': mark,
        'school_pay_code': school_pay_code,
        'exam_records': exam_records,
        'test_records': student_test_records,
        'is_primary_4_7': is_primary_4_7,
        'total_students': total_students,
        'allowed_classes': allowed_classes,  
        'class_name': class_name,
        'student_fee': student_fee,
        'student_lin': student_lin,
        'current_date': current_date,
        'exam_records': student_records,
        'current_position': student_records[0]['position'] if student_records else None,
        'show_agg_column': show_agg_column,
        'next_term_start': next_term_start.value if next_term_start else '',
        'next_term_end': next_term_end.value if next_term_end else '',
        'brooms_count': brooms_count.value if brooms_count else '0',
        'toilet_paper_count': toilet_paper_count.value if toilet_paper_count else '0',
        'student_fee': student_fee,
        'student_name': student_name, 
        'learner_lin': student.get_learner_lin,
    }

    # Render the HTML template
    html_string = render_to_string('quiz/pdf_exam_report.html', context, request=request)

    # Generate and return the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Exam_Results_{student.get_name}.pdf"'

    # Generate PDF with the correct base URL for static assets
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response

# exam folder
@login_required(login_url='adminlogin')
def print_exams_folder(request, class_name,):
    # Get all students in the class
    is_primary_4_7 = class_name in ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]
    students = Student.objects.filter(assigned_class__class_name=class_name)
    school_pay_code = Configuration.objects.filter(key='school_pay_code').first().value if Configuration.objects.filter(key='school_pay_code').exists() else 'Not Set'
    student_fee = Configuration.objects.filter(key=f"{class_name.lower()}_fee").first().value if Configuration.objects.filter(key=f"{class_name.lower()}_fee").exists() else '0'
    current_date = datetime.now().strftime('%B %d, %Y')
    next_term_start = Configuration.objects.filter(key='next_term_start').first()
    next_term_end = Configuration.objects.filter(key='next_term_end').first()
    brooms_count = Configuration.objects.filter(key='brooms_count').first()
    toilet_paper_count = Configuration.objects.filter(key='toilet_paper_count').first()
    allowed_classes = ["Primary 4", "Primary 5", "Primary 6", "Primary 7"]
    show_agg_column = class_name in allowed_classes

    # Fetch marks for all students in the same class
    class_marks = Marks.objects.filter(student__assigned_class__class_name=class_name, exam__isnull=False)

    # Fetch the fees for each primary class
    primary_1_fee = Configuration.objects.filter(key='primary_1_fee').first()
    primary_2_fee = Configuration.objects.filter(key='primary_2_fee').first()
    primary_3_fee = Configuration.objects.filter(key='primary_3_fee').first()
    primary_4_fee = Configuration.objects.filter(key='primary_4_fee').first()
    primary_5_fee = Configuration.objects.filter(key='primary_5_fee').first()
    primary_6_fee = Configuration.objects.filter(key='primary_6_fee').first()
    primary_7_fee = Configuration.objects.filter(key='primary_7_fee').first()

    # Fee mapping
    fee_mapping = {
        "Primary 1": primary_1_fee.value if primary_1_fee else '0',
        "Primary 2": primary_2_fee.value if primary_2_fee else '0',
        "Primary 3": primary_3_fee.value if primary_3_fee else '0',
        "Primary 4": primary_4_fee.value if primary_4_fee else '0',
        "Primary 5": primary_5_fee.value if primary_5_fee else '0',
        "Primary 6": primary_6_fee.value if primary_6_fee else '0',
        "Primary 7": primary_7_fee.value if primary_7_fee else '0',
    }

    # Get the fee for the student's class
    student_fee = fee_mapping.get(class_name, 0)

    if isinstance(student_fee, str) and ':' in student_fee:
        student_fee = student_fee.split(':')[1]

    # Create a memory buffer for the ZIP file
    zip_buffer = BytesIO()


    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for student in students:
            # Fetch marks for the student
            student_marks = Marks.objects.filter(student=student, exam__isnull=False)
            test_marks = Marks.objects.filter(student=student, test__isnull=False)
            if not student_marks.exists():
                continue

             # Subject abbreviations for exams
            subject_abbreviations = {
               "MATHEMATICS": "MATHS",
               "ENGLISH": "ENGLISH",
               "LITERACY 1": "LITERACY 1",
               "RELIGIOUS EDUCATION": "R.E",
               "READING": "READING",
               "LUGANDA": "LUGANDA",
               "WRITING (LIT ll)": "WRITING (LIT 11)",
               "SCIENCE": "SCIENCE",
               "SOCIAL STUDIES": "SOCIAL STUDIES",
            }

            class_marks = Marks.objects.filter(student__assigned_class=student.assigned_class, exam__isnull=False)

            exam_records = []

            student_marks = Marks.objects.filter(student=student, exam__isnull=False)

            for class_mark in class_marks:
                subject_marks = class_mark.subject_marks or []
                exam = class_mark.exam
                exam_name = f"{exam.year} - {exam.term}" if exam else "N/A"

                exam_record = {
                    'student_name': f"{class_mark.student.user.first_name} {class_mark.student.user.last_name}",
                    'exam_name': exam_name,
                    'year': exam.year if exam else None,
                    'term': exam.term if exam else None,
                    'subject_marks': [],
                    'total_marks': 0,
                    'total_full_marks': 0,
                    'total_aggregate': 0,
                    'div': None,
                }

                total_marks = 0
                total_full_marks = 0
                total_aggregate = 0

                for subject in subject_marks:
                    subject_id = subject.get('subject_id')
                    subject_obj = Subject.objects.filter(id=subject_id).first()
                    if subject_obj:
                        full_name = subject_obj.subject_name
                        abbreviated_name = subject_abbreviations.get(full_name, full_name)
                        marks = int(subject.get('marks', 0))
                        remarks = calculate_remarks(marks)
                        aggregate = calculate_aggregate(marks)

                        total_marks += marks
                        total_full_marks += 100  # Assuming full marks per subject is 100
                        total_aggregate += aggregate

                        exam_record['subject_marks'].append({
                            'name': abbreviated_name,
                            'marks': marks,
                            'remarks': remarks,
                            'aggregate': aggregate,
                        })

                exam_record['total_marks'] = total_marks
                exam_record['total_full_marks'] = total_full_marks
                exam_record['total_aggregate'] = total_aggregate
                exam_record['div'] = calculate_division(total_aggregate)
                exam_records.append(exam_record)

            # Sort exam records based on total marks
            exam_records.sort(key=lambda x: x['total_marks'], reverse=True)    

            rank = 0
            previous_total = None
            current_position = None

            total_students = len(class_marks)

            for exam_record in exam_records:
                rank += 1
                if exam_record['total_marks'] != previous_total:
                    current_position = rank
                exam_record['position'] = current_position
                previous_total = exam_record['total_marks'] 

            student_records = [record for record in exam_records if record['student_id'] == student.id]

            # Fetch the class of the current student
            student_class = student.assigned_class if hasattr(student, 'assigned_class') else None
            # Fetch marks for all students in the same class for relevant tests
            all_class_marks = Marks.objects.filter(student__assigned_class=student.assigned_class, test__isnull=False)


            # Define subject abbreviations
            subject_abbreviations = {
               "MATHEMATICS": "MTC",
               "ENGLISH": "ENG",
               "LITERACY 1": "LIT 1A",
               "RELIGIOUS EDUCATION": "C.R.E",
               "READING": "READ",
               "LUGANDA": "LUG",
               "WRITING (LIT ll)": "WRITING",
               "SCIENCE": "SCI",
               "SOCIAL STUDIES": "SST",
            }

            # Group test records by month and term
            test_records_by_month_term = defaultdict(list)

            for class_mark in all_class_marks:
                subject_marks = class_mark.subject_marks or []
                month = class_mark.test.month if class_mark.test else None
                term = class_mark.test.term if class_mark.test else None

                test_record = {
                    'student': class_mark.student.get_name,
                    'month': month,
                    'term': term,
                    'subject_marks': [],
                    'total_marks': 0,
                    'total_aggregate': 0,
                    'div': None,
                }

                total_aggregate = 0
                total_marks = 0

                for subject in subject_marks:
                    subject_id = subject.get('subject_id')
                    subject_obj = Subject.objects.filter(id=subject_id).first()
                    if subject_obj:
                       full_name = subject_obj.subject_name
                       abbreviated_name = subject_abbreviations.get(full_name, full_name)
                       marks = int(subject.get('marks', 0))
                       aggregate = calculate_aggregate(marks)  # Compute aggregate for the subject
                
                       total_marks += marks
                       total_aggregate += aggregate

                       test_record['subject_marks'].append({
                          'name': abbreviated_name,
                          'marks': marks,
                          'aggregate': aggregate,  # Subject aggregate
                        })

                test_record['total_marks'] = total_marks
                test_record['total_aggregate'] = total_aggregate  # Sum of all subject aggregates
                test_record['div'] = calculate_division(total_aggregate)  # Compute division based on total aggregate

                # Group by month and term
                test_records_by_month_term[(month, term)].append(test_record)

            # Assign positions within each month and term group
            for (month, term), records in test_records_by_month_term.items():
                # Sort by total marks (descending order)
                records.sort(key=lambda x: x['total_marks'], reverse=True)
                # Assign positions
                for idx, record in enumerate(records):
                    record['position'] = idx + 1

            # Filter records for the current student
            student_test_records = [
                record for records in test_records_by_month_term.values() for record in records
               if record['student'] == student.get_name
            ]
   
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                 for student in students:
            # Render the HTML to a string
                     context = {
                        'student_name': f"{student.user.first_name} {student.user.last_name}",
                        'school_pay_code': school_pay_code,
                        'exam_records': exam_records,
                        'test_records': student_test_records,
                        'is_primary_4_7': is_primary_4_7,
                        'total_students': total_students,
                        'allowed_classes': allowed_classes,  
                        'class_name': class_name,
                        'student_fee': student_fee,
                        'current_date': current_date,
                        'exam_records': student_records,
                        'current_position': student_records[0]['position'] if student_records else None,
                        'show_agg_column': show_agg_column,
                        'next_term_start': next_term_start.value if next_term_start else '',
                        'next_term_end': next_term_end.value if next_term_end else '',
                        'brooms_count': brooms_count.value if brooms_count else '0',
                        'toilet_paper_count': toilet_paper_count.value if toilet_paper_count else '0',
                        'student_fee': student_fee,
                        'student_name': student.get_name, 
                        'learner_lin': student.get_learner_lin,
                    }

                     # Render the HTML template
                     html_string = render_to_string('quiz/pdf_exam_report.html', context, request=request)

                     # Generate the PDF
                     pdf_buffer = BytesIO()
                     HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(pdf_buffer)
                     pdf_buffer.seek(0)

                     # Add the PDF to the ZIP file
                     pdf_filename = f"{student.user.first_name}_{student.user.last_name}_Exam_Report.pdf"
                     zip_file.writestr(pdf_filename, pdf_buffer.read())

            # Finalize the ZIP file
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{class_name}_Exam_Reports.zip"'
            return response



# Configurations
def configurations_view(request):

    def get_fee_value(key):
        """Helper function to extract fee value from Configuration."""
        fee_config = Configuration.objects.filter(key=key).first()
        if fee_config and ':' in fee_config.value:
            return fee_config.value.split(':')[1].strip()
        return fee_config.value if fee_config else '0'

    if request.method == 'POST':
        # Fetch School Pay Code
        school_pay_code = request.POST.get('school_pay_code')

        # Fetch Term Start and End Dates
        next_term_start = request.POST.get('next_term_start')
        next_term_end = request.POST.get('next_term_end')

        # Fetch Brooms and Toilet Paper counts
        brooms_count = request.POST.get('brooms_count')
        toilet_paper_count = request.POST.get('toilet_paper_count')

        # Update or create configurations for School Pay Code
        config_school_pay, created = Configuration.objects.get_or_create(key='school_pay_code')
        config_school_pay.value = school_pay_code
        config_school_pay.save()

        # Update or create configurations for Term Start Date
        config_start, created = Configuration.objects.get_or_create(key='next_term_start')
        config_start.value = next_term_start
        config_start.save()

        # Update or create configurations for Term End Date
        config_end, created = Configuration.objects.get_or_create(key='next_term_end')
        config_end.value = next_term_end
        config_end.save()

        # Update or create configurations for Brooms count
        config_brooms, created = Configuration.objects.get_or_create(key='brooms_count')
        config_brooms.value = brooms_count
        config_brooms.save()

        # Update or create configurations for Toilet Paper count
        config_toilet_paper, created = Configuration.objects.get_or_create(key='toilet_paper_count')
        config_toilet_paper.value = toilet_paper_count
        config_toilet_paper.save()

        # Helper function to sanitize fee values
        def sanitize_fee_value(fee_value):
            if ':' in fee_value:
                return fee_value.split(':')[1].strip()
            return fee_value.strip()

        # Fetch and sanitize fees for each Primary class
        primary_1_fee = sanitize_fee_value(request.POST.get('primary_1_fee', '0'))
        primary_2_fee = sanitize_fee_value(request.POST.get('primary_2_fee', '0'))
        primary_3_fee = sanitize_fee_value(request.POST.get('primary_3_fee', '0'))
        primary_4_fee = sanitize_fee_value(request.POST.get('primary_4_fee', '0'))
        primary_5_fee = sanitize_fee_value(request.POST.get('primary_5_fee', '0'))
        primary_6_fee = sanitize_fee_value(request.POST.get('primary_6_fee', '0'))
        primary_7_fee = sanitize_fee_value(request.POST.get('primary_7_fee', '0'))

        # Save the sanitized fees
        Configuration.objects.update_or_create(key='primary_1_fee', defaults={'value': primary_1_fee})
        Configuration.objects.update_or_create(key='primary_2_fee', defaults={'value': primary_2_fee})
        Configuration.objects.update_or_create(key='primary_3_fee', defaults={'value': primary_3_fee})
        Configuration.objects.update_or_create(key='primary_4_fee', defaults={'value': primary_4_fee})
        Configuration.objects.update_or_create(key='primary_5_fee', defaults={'value': primary_5_fee})
        Configuration.objects.update_or_create(key='primary_6_fee', defaults={'value': primary_6_fee})
        Configuration.objects.update_or_create(key='primary_7_fee', defaults={'value': primary_7_fee})

        # Success message
        messages.success(request, "Configurations updated successfully!")
        return redirect('configurations')  # Redirect to the same page after saving

    # Fetch current configurations
    school_pay_code = Configuration.objects.filter(key='school_pay_code').first()
    next_term_start = Configuration.objects.filter(key='next_term_start').first()
    next_term_end = Configuration.objects.filter(key='next_term_end').first()
    brooms_count = Configuration.objects.filter(key='brooms_count').first()
    toilet_paper_count = Configuration.objects.filter(key='toilet_paper_count').first()

    
    # Fetch current fee configurations
    primary_1_fee = get_fee_value('primary_1_fee')
    primary_2_fee = get_fee_value('primary_2_fee')
    primary_3_fee = get_fee_value('primary_3_fee')
    primary_4_fee = get_fee_value('primary_4_fee')
    primary_5_fee = get_fee_value('primary_5_fee')
    primary_6_fee = get_fee_value('primary_6_fee')
    primary_7_fee = get_fee_value('primary_7_fee')

    # Pass values to template
    context = {
        'school_pay_code': school_pay_code.value if school_pay_code else '',
        'next_term_start': next_term_start.value if next_term_start else '',
        'next_term_end': next_term_end.value if next_term_end else '',
        'brooms_count': brooms_count.value if brooms_count else '0',
        'toilet_paper_count': toilet_paper_count.value if toilet_paper_count else '0',
        'primary_1_fee': primary_1_fee,
        'primary_2_fee': primary_2_fee,
        'primary_3_fee': primary_3_fee,
        'primary_4_fee': primary_4_fee,
        'primary_5_fee': primary_5_fee,
        'primary_6_fee': primary_6_fee,
        'primary_7_fee': primary_7_fee,
    }
    return render(request, 'quiz/configurations.html', context)

# calculate remarks
# Grading function based on the grading scheme with remarks
def calculate_remarks(mark):
    if mark < 40:
        return "FAIL"
    elif 40 <= mark <= 44:
        return "PASS"
    elif 45 <= mark <= 49:
        return "MARGINAL PASS"
    elif 50 <= mark <= 59:
        return "FAIR"
    elif 60 <= mark <= 69:
        return "FAIRLY GOOD"
    elif 70 <= mark <= 74:
        return "GOOD"
    elif 75 <= mark <= 79:
        return "VERY GOOD"
    elif 80 <= mark <= 89:
        return "EXCELLENT"
    elif 90 <= mark <= 100:
        return "EXCEPTIONAL"
    return "UNKNOWN"



# test view
@login_required(login_url='adminlogin')
def admin_marked_students_tests_view(request):
    # Fetch all classes in their desired order
    classes = Class.objects.all().order_by('id')  # Adjust 'id' for your desired ordering field
    selected_class = request.GET.get('selected_class', None)

    # Initialize an ordered dictionary for grouping students
    marked_students_by_class = OrderedDict()
    for class_obj in classes:
        class_name = class_obj.class_name
        marked_students_by_class[class_name] = []  # Empty list for each class

    # Fetch all marks and filter for tests
    marks = Marks.objects.select_related('student', 'test').filter(test__isnull=False)

    # Group students by class
    for mark in marks:
        student = mark.student
        student_class = student.assigned_class.class_name if student.assigned_class else "Unassigned"
        if student_class not in marked_students_by_class:
            marked_students_by_class[student_class] = []

        # Extract subject marks
        subject_marks_dict = {}
        for item in mark.subject_marks:
            try:
                subject_id = int(item['subject_id'])
                marks = int(item['marks'])
                subject_name = Subject.objects.get(id=subject_id).subject_name
                subject_marks_dict[subject_name] = marks
            except ValueError:
                subject_marks_dict["Unknown"] = None

        # Append student data to respective class group
        marked_students_by_class[student_class].append({
            'name': student.get_name,
            'profile_pic': student.profile_pic.url if student.profile_pic else None,
            'test': str(mark.test) if mark.test else "N/A",
            'subject_marks': subject_marks_dict,
            'mark': mark
        })

    # Sort students alphabetically within each class
    for class_name, students in marked_students_by_class.items():
        marked_students_by_class[class_name] = sorted(students, key=lambda x: x['name'])

    context = {
        'marked_students_by_class': marked_students_by_class,
        'classes': classes,
        'selected_class': selected_class,
    }
    return render(request, 'quiz/admin_marked_students_tests.html', context)
    

# edit marks
# Admin - View Marks
@login_required(login_url='adminlogin')
def admin_edit_marks_view(request, mark_id):
    mark = get_object_or_404(Marks, id=mark_id)
    student = mark.student

    # Fetch the class of the current student
    student_class = student.assigned_class if hasattr(student, 'assigned_class') else None

    if not student_class:
        return render(request, 'quiz/admin_edit_marks.html', {
            'mark': mark,
            'test_records': [],
            'class_name': "Unassigned",
        })

    class_name = student_class.class_name

    # Fetch marks for all students in the same class for relevant tests
    all_class_marks = Marks.objects.filter(student__assigned_class=student_class, test__isnull=False)

    # Define subject abbreviations
    subject_abbreviations = {
        "MATHEMATICS": "MTC",
        "ENGLISH": "ENG",
        "LITERACY 1": "LIT 1A",
        "RELIGIOUS EDUCATION": "C.R.E",
        "READING": "READ",
        "LUGANDA": "LUG",
        "WRITING (LIT ll)": "WRITING",
        "SCIENCE": "SCI",
        "SOCIAL STUDIES": "SST",
    }

    # Group test records by month and term
    test_records_by_month_term = defaultdict(list)

    for class_mark in all_class_marks:
        subject_marks = class_mark.subject_marks or []
        month = class_mark.test.month if class_mark.test else None
        term = class_mark.test.term if class_mark.test else None

        test_record = {
            'student': class_mark.student.get_name,
            'month': month,
            'term': term,
            'subject_marks': [],
            'total_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                aggregate = calculate_aggregate(marks)  # Compute aggregate for the subject
                
                total_marks += marks
                total_aggregate += aggregate

                test_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'aggregate': aggregate,  # Subject aggregate
                })

        test_record['total_marks'] = total_marks
        test_record['total_aggregate'] = total_aggregate  # Sum of all subject aggregates
        test_record['div'] = calculate_division(total_aggregate)  # Compute division based on total aggregate

        # Group by month and term
        test_records_by_month_term[(month, term)].append(test_record)

    # Assign positions within each month and term group
    for (month, term), records in test_records_by_month_term.items():
        # Sort by total marks
        records.sort(key=lambda x: x['total_marks'], reverse=True)
        # Assign positions
        for idx, record in enumerate(records):
            record['position'] = idx + 1

    # Filter records for the current student
    student_test_records = [
        record for records in test_records_by_month_term.values() for record in records
        if record['student'] == student.get_name
    ]

    return render(request, 'quiz/admin_edit_marks.html', {
        'mark': mark,
        'test_records': student_test_records,
        'class_name': class_name,
    })

# Grading function based on the grading scheme
def calculate_aggregate(mark):
    if mark < 40:
        return 9  # F9
    elif 40 <= mark <= 44:
        return 8  # P8
    elif 45 <= mark <= 49:
        return 7  # P7
    elif 50 <= mark <= 59:
        return 6  # C6
    elif 60 <= mark <= 69:
        return 5  # C5
    elif 70 <= mark <= 74:
        return 4  # C4
    elif 75 <= mark <= 79:
        return 3  # C3
    elif 80 <= mark <= 89:
        return 2  # D2
    elif 90 <= mark <= 100:
        return 1  # D1
    return 9  # Default to F9 for invalid marks

# Division determination based on total aggregate
def calculate_division(total_agg):
    if total_agg <= 12:
        return "D1"
    elif 13 <= total_agg <= 23:
        return "D2"
    elif 24 <= total_agg <= 29:
        return "D3"
    else:
        return "D4"

# print test results
@login_required(login_url='adminlogin')
def generate_pdf(request, mark_id):
    # Fetch the mark record
    mark = get_object_or_404(Marks, id=mark_id)
    student = mark.student
    student_class = student.assigned_class if hasattr(student, 'assigned_class') else None

    if not student_class:
        return HttpResponse("Student is not assigned to a class.", status=400)

    class_name = student_class.class_name
    all_class_marks = Marks.objects.filter(student__assigned_class=student_class, test__isnull=False)

    subject_abbreviations = {
        "MATHEMATICS": "MTC",
        "ENGLISH": "ENG",
        "LITERACY 1": "LIT 1A",
        "RELIGIOUS EDUCATION": "C.R.E",
        "READING": "READ",
        "LUGANDA": "LUG",
        "WRITING (LIT ll)": "WRITING",
        "SCIENCE": "SCI",
        "SOCIAL STUDIES": "SST",
    }

    test_records_by_month_term = defaultdict(list)

    for class_mark in all_class_marks:
        subject_marks = class_mark.subject_marks or []
        month = class_mark.test.month if class_mark.test else None
        term = class_mark.test.term if class_mark.test else None

        test_record = {
            'student': class_mark.student.get_name,
            'month': month,
            'term': term,
            'subject_marks': [],
            'total_marks': 0,
            'total_aggregate': 0,
            'div': None,
        }

        total_aggregate = 0
        total_marks = 0

        for subject in subject_marks:
            subject_id = subject.get('subject_id')
            subject_obj = Subject.objects.filter(id=subject_id).first()
            if subject_obj:
                full_name = subject_obj.subject_name
                abbreviated_name = subject_abbreviations.get(full_name, full_name)
                marks = int(subject.get('marks', 0))
                aggregate = calculate_aggregate(marks)

                total_marks += marks
                total_aggregate += aggregate

                test_record['subject_marks'].append({
                    'name': abbreviated_name,
                    'marks': marks,
                    'aggregate': aggregate,
                })

        test_record['total_marks'] = total_marks
        test_record['total_aggregate'] = total_aggregate
        test_record['div'] = calculate_division(total_aggregate)
        test_records_by_month_term[(month, term)].append(test_record)

    for (month, term), records in test_records_by_month_term.items():
        records.sort(key=lambda x: x['total_marks'], reverse=True)
        for idx, record in enumerate(records):
            record['position'] = idx + 1

    student_test_records = [
        record for records in test_records_by_month_term.values() for record in records
        if record['student'] == student.get_name
    ]

    all_subjects = {
        subject['name'] for record in student_test_records for subject in record['subject_marks']
    }
    subjects = sorted(all_subjects)

    student_name = student.get_name
    html_string = render_to_string('quiz/print_results.html', {
        'mark': mark,
        'test_records': student_test_records,
        'subjects': subjects,
        'class_name': class_name,
        'student_name': student_name,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Test_Marks_{student_name}.pdf"'
    HTML(string=html_string).write_pdf(response)

    return response


# generate folder for tests
@login_required(login_url='adminlogin')
def print_tests_folder(request, class_name):
    """
    Generate and return a ZIP file containing test result PDFs for all students in a class.
    """
    students = Student.objects.filter(assigned_class__class_name=class_name)
    zip_buffer = BytesIO()

    subject_abbreviations = {
        "MATHEMATICS": "MTC",
        "ENGLISH": "ENG",
        "LITERACY 1": "LIT 1A",
        "RELIGIOUS EDUCATION": "C.R.E",
        "READING": "READ",
        "LUGANDA": "LUG",
        "WRITING (LIT ll)": "WRITING",
        "SCIENCE": "SCI",
        "SOCIAL STUDIES": "SST",
    }

    # Fetch all test records
    all_test_records_by_month_term = defaultdict(list)

    for student in students:
        all_class_marks = Marks.objects.filter(student=student, test__isnull=False)

        for class_mark in all_class_marks:
            subject_marks = class_mark.subject_marks or []
            month = class_mark.test.month if class_mark.test else None
            term = class_mark.test.term if class_mark.test else None

            test_record = {
                'student': class_mark.student.get_name,
                'month': month,
                'term': term,
                'subject_marks': [],
                'total_marks': 0,
                'total_aggregate': 0,
                'div': None,
            }

            total_marks = 0
            total_aggregate = 0

            for subject in subject_marks:
                subject_id = subject.get('subject_id')
                subject_obj = Subject.objects.filter(id=subject_id).first()
                if subject_obj:
                    full_name = subject_obj.subject_name
                    abbreviated_name = subject_abbreviations.get(full_name, full_name)
                    marks = int(subject.get('marks', 0))
                    aggregate = calculate_aggregate(marks)

                    total_marks += marks
                    total_aggregate += aggregate

                    test_record['subject_marks'].append({
                        'name': abbreviated_name,
                        'marks': marks,
                        'aggregate': aggregate,
                    })

            test_record['total_marks'] = total_marks
            test_record['total_aggregate'] = total_aggregate
            test_record['div'] = calculate_division(total_aggregate)
            all_test_records_by_month_term[(month, term)].append(test_record)

    # Assign positions
    for (month, term), records in all_test_records_by_month_term.items():
        records.sort(key=lambda x: x['total_marks'], reverse=True)
        for idx, record in enumerate(records):
            record['position'] = idx + 1  # Position starts from 1

    # Create a ZIP file and add PDFs for each student
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for student in students:
            student_test_records = [
                record for records in all_test_records_by_month_term.values() for record in records
                if record['student'] == student.get_name
            ]
            student_test_records.sort(key=lambda x: (x['month'], x['term']))

            all_subjects = {
                subject['name'] for record in student_test_records for subject in record['subject_marks']
            }
            subjects = sorted(all_subjects)

            student_name = student.get_name
            html_string = render_to_string('quiz/print_results.html', {
                'test_records': student_test_records,
                'subjects': subjects,
                'class_name': class_name,
                'student_name': student_name,
            })

            pdf_filename = f"{student_name}_Test_Marks.pdf"
            pdf = HTML(string=html_string).write_pdf()
            zip_file.writestr(pdf_filename, pdf)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{class_name}_Test_Folder.zip"'
    return response



#COURSE MANAGEMENT
# Admin view for courses
@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request, 'quiz/admin_course.html')

# Add new course (Admin)
@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm = forms.CourseForm()
    if request.method == 'POST':
        courseForm = forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request, 'quiz/admin_add_course.html', {'courseForm': courseForm})

# Admin view for all courses
@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request, 'quiz/admin_view_course.html', {'courses': courses})

# Delete course (Admin)
@login_required(login_url='adminlogin')
def delete_course_view(request, pk):
    course = models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')


# QUESTION MANAGEMENT 
# Admin view for questions
@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request, 'quiz/admin_question.html')

# Add new question (Admin)
@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm = forms.QuestionForm()
    if request.method == 'POST':
        questionForm = forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = models.Course.objects.get(id=request.POST.get('courseID'))
            question.course = course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-question')
    return render(request, 'quiz/admin_add_question.html', {'questionForm': questionForm})

# Admin view for all questions
@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses = models.Course.objects.all()
    return render(request, 'quiz/admin_view_question.html', {'courses': courses})

# View specific question details (Admin)
@login_required(login_url='adminlogin')
def view_question_view(request, pk):
    questions = models.Question.objects.all().filter(course_id=pk)
    return render(request, 'quiz/view_question.html', {'questions': questions})

# Delete question (Admin)
@login_required(login_url='adminlogin')
def delete_question_view(request, pk):
    question = models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

# Admin view for student marks
@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students = SMODEL.Student.objects.all()
    return render(request, 'quiz/admin_view_student_marks.html', {'students': students})

# Admin view for marks of a specific student
@login_required(login_url='adminlogin')
def admin_view_marks_view(request, pk):
    courses = models.Course.objects.all()
    response = render(request, 'quiz/admin_view_marks.html', {'courses': courses})
    response.set_cookie('student_id', str(pk))
    return response

# Admin view for checking marks of a student
@login_required(login_url='adminlogin')
def admin_check_marks_view(request, pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student = SMODEL.Student.objects.get(id=student_id)

    results = models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, 'quiz/admin_check_marks.html', {'results': results})


# Other views (About us, Contact us)
def aboutus_view(request):
    return render(request, 'quiz/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name = sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name) + ' || ' + str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently=False)
            return render(request, 'quiz/contactussuccess.html')
    return render(request, 'quiz/contactus.html', {'form': sub})

