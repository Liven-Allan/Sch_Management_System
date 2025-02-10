from django.shortcuts import render,redirect,get_object_or_404,reverse
from django.http import JsonResponse
import json, logging
from . import forms
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from quiz import models as QMODEL
from student import models as SMODEL
from quiz import forms as QFORM
from .models import Teacher, Marks
from student.models import Student
from .forms import MarksForm
from quiz.models import Exam, Test, Subject

# Configure logging
logger = logging.getLogger(__name__)

#for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'teacher/teacherclick.html')

def teacher_signup_view(request):
    userForm=forms.TeacherUserForm()
    teacherForm=forms.TeacherForm()
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=forms.TeacherUserForm(request.POST)
        teacherForm=forms.TeacherForm(request.POST,request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacher=teacherForm.save(commit=False)
            teacher.user=user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect('teacherlogin')
    return render(request,'teacher/teachersignup.html',context=mydict)



def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    return redirect('teacher-classes') 

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request,'teacher/teacher_exam.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm=QFORM.CourseForm()
    if request.method=='POST':
        courseForm=QFORM.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-exam')
    return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/teacher/teacher-view-exam')

@login_required(login_url='adminlogin')
def teacher_question_view(request):
    return render(request,'teacher/teacher_question.html')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    questionForm=QFORM.QuestionForm()
    if request.method=='POST':
        questionForm=QFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question=questionForm.save(commit=False)
            course=QMODEL.Course.objects.get(id=request.POST.get('courseID'))
            question.course=course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-question')
    return render(request,'teacher/teacher_add_question.html',{'questionForm':questionForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses= QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_question.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request,pk):
    questions=QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request,'teacher/see_question.html',{'questions':questions})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request,pk):
    question=QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')

# view classes
@login_required(login_url='teacherlogin')
def teacher_classes_view(request):
    try:
        # Fetch the Teacher object associated with the logged-in user
        teacher = Teacher.objects.get(user=request.user)

        # Get the assigned classes for the teacher
        assigned_classes = teacher.assigned_classes.all()

        # Fetch students for each assigned class with counts
        students_by_class = {}
        for class_obj in assigned_classes:
            students = Student.objects.filter(assigned_class=class_obj)

            # Annotate each student with exam and test counts
            for student in students:
                student.exam_count = Marks.objects.filter(student=student, exam__isnull=False).count()
                student.test_count = Marks.objects.filter(student=student, test__isnull=False).count()

            students_by_class[class_obj.class_name] = students

        return render(request, 'teacher/teacher_view_classes.html', {'students_by_class': students_by_class})
    except Teacher.DoesNotExist:
        return render(request, 'teacher/teacher_view_classes.html', {'error': 'You are not assigned to any classes.'})


# add exam marks    
@login_required(login_url='teacherlogin')
def add_marks_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = MarksForm(request.POST or None)

    # Fetch all exams
    exams = Exam.objects.all()

    # Handle AJAX GET or POST requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            try:
                # Parse the incoming JSON data
                data = json.loads(request.body)  # Use request.body for raw data
                marks_data = data.get('subject_marks')

                if not marks_data:
                    return JsonResponse({'error': 'No marks data received.'}, status=400)

                exam_year = data.get('exam_year')
                if not exam_year:
                    return JsonResponse({'error': 'No exam year selected.'}, status=400)

                try:
                    exam = Exam.objects.get(id=exam_year)  # Ensure the exam is selected
                except Exam.DoesNotExist:
                    return JsonResponse({'error': f"Exam with ID {exam_year} does not exist."}, status=400)

                # Handle saving marks with multiple subjects in one record
                Marks.objects.create(
                    student=student,
                    exam=exam,
                    subject_marks=marks_data,  # Store JSON data of subjects and marks
                )

                return JsonResponse({'message': 'Marks saved successfully'})

            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data received.'}, status=400)

        elif request.method == 'GET':
            # You can return some dynamic data if needed for AJAX GET requests
            return JsonResponse({'message': 'This is a placeholder for AJAX GET request handling.'})

        return JsonResponse({'error': 'Invalid AJAX request method.'}, status=400)

    # Handle normal POST request (form submission)
    if request.method == 'POST' and form.is_valid():
        marks_type = form.cleaned_data['marks_type']
        subject_marks = form.cleaned_data['subject_marks']

        try:
            marks_data = json.loads(subject_marks)  # Parse the JSON
        except json.JSONDecodeError:
            messages.error(request, "Invalid marks data submitted.")
            return render(request, 'teacher/add_marks.html', {'form': form, 'student': student, 'exams': exams})

        # Handle saving marks
        Marks.objects.create(
            student=student,
            exam=form.cleaned_data.get('exam'),  # Assuming exam is part of the form
            subject_marks=marks_data,  # Store JSON data
        )

        messages.success(request, "Marks saved successfully.")
        return redirect('teacher-classes')

    # Render the form for normal GET requests
    return render(request, 'teacher/add_marks.html', {'form': form, 'student': student, 'exams': exams})

# add test marks
@login_required(login_url='teacherlogin')
def add_test_marks_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = MarksForm(request.POST or None)

    # Fetch all tests
    tests = Test.objects.all()  # Assuming `Test` is a model similar to `Exam`

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                marks_data = data.get('subject_marks')

                if not marks_data:
                    return JsonResponse({'error': 'No marks data received.'}, status=400)

                test_id = data.get('test_id')
                if not test_id:
                    return JsonResponse({'error': 'No test selected.'}, status=400)

                try:
                    test = Test.objects.get(id=test_id)
                except Test.DoesNotExist:
                    return JsonResponse({'error': f"Test with ID {test_id} does not exist."}, status=400)

                Marks.objects.create(
                    student=student,
                    test=test,  # Assuming the `Marks` model has a `test` field
                    subject_marks=marks_data,
                )

                return JsonResponse({'message': 'Test marks saved successfully'})

            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data received.'}, status=400)

    if request.method == 'POST' and form.is_valid():
        subject_marks = form.cleaned_data['subject_marks']

        try:
            marks_data = json.loads(subject_marks)
        except json.JSONDecodeError:
            messages.error(request, "Invalid marks data submitted.")
            return render(request, 'teacher/add_test_marks.html', {'form': form, 'student': student, 'tests': tests})

        Marks.objects.create(
            student=student,
            test=form.cleaned_data.get('test'),
            subject_marks=marks_data,
        )

        messages.success(request, "Test marks saved successfully.")
        return redirect('teacher-classes')

    return render(request, 'teacher/add_test_marks.html', {'form': form, 'student': student, 'tests': tests})


# load subjects
@login_required(login_url='teacherlogin')
def load_subjects(request):
    exam_id = request.GET.get('exam_id')
    student_id = request.GET.get('student_id')
    subjects = []

    if exam_id and student_id:
        # Fetch the student and their class
        student = get_object_or_404(Student, id=student_id)
        student_class = student.assigned_class  # Fetch student's class
        subjects = Subject.objects.filter(class_name=student_class)  # Filter subjects by student's class

    # Return the subjects as JSON data
    return JsonResponse({"subjects": [{"id": subj.id, "name": subj.subject_name} for subj in subjects]})

# Marked Students View
@login_required(login_url='teacherlogin')
def marked_students_view(request):
    class_name = request.GET.get('class_name')  # Retrieve the class name if available
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        assigned_classes = teacher.assigned_classes.all()

        # Filter records where 'exam' is not null
        marks = Marks.objects.select_related('student', 'exam', 'test').filter(
            student__assigned_class__in=assigned_classes,
            exam__isnull=False  # Only include records where 'exam' is not null
        )

        marked_students_by_class = {}
        for mark in marks:
            student = mark.student
            student_class = student.assigned_class.class_name if student.assigned_class else "Unassigned"

            if student_class not in marked_students_by_class:
                marked_students_by_class[student_class] = []

            subject_marks_dict = {}
            for item in mark.subject_marks:
                try:
                    subject_id = int(item['subject_id'])
                    marks = int(item['marks'])
                    # Fetch the subject name using the subject_id
                    subject_name = Subject.objects.get(id=subject_id).subject_name
                    subject_marks_dict[subject_name] = marks
                except ValueError:
                    subject_marks_dict["Unknown"] = None  # Handle invalid data

            marked_students_by_class[student_class].append({
                'name': student.get_name,
                'profile_pic': student.profile_pic.url if student.profile_pic else None,
                'exam': str(mark.exam) if mark.exam else "N/A",
                'subject_marks': subject_marks_dict,
                'mark': mark
            })

        context = {
            'marked_students_by_class': marked_students_by_class,
        }
        return render(request, 'teacher/marked_students.html', context)
    except Teacher.DoesNotExist:
        return render(request, 'teacher/marked_students.html', {'error': 'You are not assigned to any classes.'})


# delete mark
@login_required(login_url='teacherlogin')
def delete_mark_view(request, mark_id):
    try:
        # Get the mark object
        mark = get_object_or_404(Marks, id=mark_id)

        # Ensure the teacher has access to delete the mark (check class assignment)
        teacher = Teacher.objects.get(user=request.user)
        if mark.student.assigned_class in teacher.assigned_classes.all():
            mark.delete()
            messages.success(request, "Mark deleted successfully.")
        else:
            messages.error(request, "You do not have permission to delete this record.")
    except Teacher.DoesNotExist:
        messages.error(request, "You are not assigned to any class.")

    return redirect('marked-students')    

# delete all classes
@login_required(login_url='teacherlogin')
def delete_all_marks_view(request, class_name):
    try:
        if request.method == "POST":
            # Ensure the teacher has access to the class
            teacher = Teacher.objects.get(user=request.user)
            assigned_class = teacher.assigned_classes.filter(class_name=class_name).first()
            if assigned_class:
                # Delete all marks for the students in the class
                Marks.objects.filter(student__assigned_class=assigned_class, test__isnull=False).delete()
                messages.success(request, f"All marks for class '{class_name}' have been deleted.")
            else:
                messages.error(request, "You do not have permission to delete records for this class.")
        else:
            messages.error(request, "Invalid request method.")
    except Teacher.DoesNotExist:
        messages.error(request, "You are not assigned to any class.")

    return redirect('marked-students-tests')  # Redirect back to the test marks view

# delete exams
@login_required(login_url='teacherlogin')
def delete_class_marks_view(request, class_name):
    try:
        if request.method == "POST":
            # Ensure the teacher has access to the class
            teacher = Teacher.objects.get(user=request.user)
            assigned_class = teacher.assigned_classes.filter(class_name=class_name).first()
            if assigned_class:
                # Delete all marks for the students in the class where 'exam' is not null
                Marks.objects.filter(student__assigned_class=assigned_class, exam__isnull=False).delete()
                messages.success(request, f"All exam marks for class '{class_name}' have been deleted.")
            else:
                messages.error(request, "You do not have permission to delete records for this class.")
        else:
            messages.error(request, "Invalid request method.")
    except Teacher.DoesNotExist:
        messages.error(request, "You are not assigned to any class.")

    return redirect('marked-students-tests')  # Redirect back to the marked students view


# Edit marks
@login_required(login_url='teacherlogin')
def edit_marks_view(request, mark_id):
    mark = get_object_or_404(Marks, id=mark_id)
    class_name = request.GET.get('class_name')  # Retrieve the class name

    # Parse the JSON field
    subject_marks = mark.subject_marks or []

    # Map subject IDs to names
    for subject in subject_marks:
        subject_id = subject.get('subject_id')
        subject_obj = Subject.objects.filter(id=subject_id).first()
        if subject_obj:
            subject['subject_name'] = subject_obj.subject_name

    if request.method == 'POST':
        updated_marks = request.POST.getlist('marks')  # List of marks
        for i, subject in enumerate(subject_marks):
            subject['marks'] = updated_marks[i]  # Update marks in JSON

        # Save the updated marks
        mark.subject_marks = subject_marks
        mark.save()
        messages.success(request, "Marks updated successfully.")

        # Redirect back to the specific class view
        return redirect(f"{reverse('marked-students')}?class_name={class_name}")

    return render(request, 'teacher/edit_marks.html', {
        'mark': mark,
        'subject_marks': subject_marks,
    })


# test
# Load subjects for a test
@login_required(login_url='teacherlogin')
def load_test_subjects(request):
    test_id = request.GET.get('test_id')
    student_id = request.GET.get('student_id')

    try:
        test = Test.objects.get(id=test_id)
        student = Student.objects.get(id=student_id)
        class_subjects = Subject.objects.filter(class_name=student.assigned_class)

        # Prepare subjects as a list of dictionaries
        subjects = [{'id': subj.id, 'name': subj.subject_name} for subj in class_subjects]
        return JsonResponse({'subjects': subjects})
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Invalid test ID'}, status=400)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Invalid student ID'}, status=400)

# maked student tests view
@login_required(login_url='teacherlogin')
def marked_students_tests_view(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        assigned_classes = teacher.assigned_classes.all()

        marks = Marks.objects.select_related('student', 'test').filter(
            student__assigned_class__in=assigned_classes,
            test__isnull=False  # Only include records where 'test' is not null
        )

        marked_students_by_class = {}
        for mark in marks:
            student = mark.student
            student_class = student.assigned_class.class_name if student.assigned_class else "Unassigned"

            if student_class not in marked_students_by_class:
                marked_students_by_class[student_class] = []

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
                'test': str(mark.test) if mark.test else "N/A",
                'subject_marks': subject_marks_dict,
                'mark': mark
            })

        context = {
            'marked_students_by_class': marked_students_by_class,
        }
        return render(request, 'teacher/marked_students_tests.html', context)
    except Teacher.DoesNotExist:
        return render(request, 'teacher/marked_students_tests.html', {'error': 'You are not assigned to any classes.'})
