from django.urls import path,include
from django.contrib import admin
from quiz import views
from django.contrib.auth.views import LogoutView,LoginView
urlpatterns = [
   
    path('admin/', admin.site.urls),
    path('teacher/',include('teacher.urls')),
    path('student/',include('student.urls')),
    


    path('',views.home_view,name=''),
    path('logout', LogoutView.as_view(template_name='quiz/logout.html'),name='logout'),
    path('aboutus', views.aboutus_view),
    path('contactus', views.contactus_view),
    path('afterlogin', views.afterlogin_view,name='afterlogin'),



    path('adminclick', views.adminclick_view),
    path('adminlogin', LoginView.as_view(template_name='quiz/adminlogin.html'),name='adminlogin'),
    path('admin-dashboard', views.admin_dashboard_view,name='admin-dashboard'),
    path('admin-teacher', views.admin_teacher_view,name='admin-teacher'),
    path('admin-view-teacher', views.admin_view_teacher_view,name='admin-view-teacher'),
    path('update-teacher/<int:pk>', views.update_teacher_view,name='update-teacher'),
    path('admin-view-pending-teacher', views.admin_view_pending_teacher_view,name='admin-view-pending-teacher'),
    path('admin-view-teacher-salary', views.admin_view_teacher_salary_view,name='admin-view-teacher-salary'),
    path('approve-teacher/<int:pk>', views.approve_teacher_view,name='approve-teacher'),
    path('reject-teacher/<int:pk>', views.reject_teacher_view,name='reject-teacher'),

    path('admin-student', views.admin_student_view,name='admin-student'),
    path('admin-students/', views.admin_students_view, name='admin-students'),
    path('delete-student/<int:student_id>/', views.delete_student, name='delete-student'),
    path('admin-teachers/', views.admin_teachers_view, name='admin-teachers'),
    # urls.py
    path('delete-teacher/<int:teacher_id>/', views.delete_teacher, name='delete-teacher'),
    path('admin-view-student', views.admin_view_student_view,name='admin-view-student'),
    path('admin-view-student-marks', views.admin_view_student_marks_view,name='admin-view-student-marks'),
    path('admin-view-marks/<int:pk>', views.admin_view_marks_view,name='admin-view-marks'),
    path('admin-check-marks/<int:pk>', views.admin_check_marks_view,name='admin-check-marks'),
    path('update-student/<int:pk>', views.update_student_view,name='update-student'),

    path('admin-course', views.admin_course_view,name='admin-course'),
    path('admin-add-course', views.admin_add_course_view,name='admin-add-course'),
    path('admin-view-course', views.admin_view_course_view,name='admin-view-course'),
    path('delete-course/<int:pk>', views.delete_course_view,name='delete-course'),

    path('admin-question', views.admin_question_view,name='admin-question'),
    path('admin-add-question', views.admin_add_question_view,name='admin-add-question'),
    path('admin-view-question', views.admin_view_question_view,name='admin-view-question'),
    path('view-question/<int:pk>', views.view_question_view,name='view-question'),
    path('delete-question/<int:pk>', views.delete_question_view,name='delete-question'),

    # me
    path('admin-classes', views.admin_classes_view, name='admin-classes'),
    path('register-teacher/', views.register_teacher_view, name='register-teacher'),   
    path('register-student/', views.register_student_view, name='register-student'),
    # classes
    path('admin-classes/', views.admin_classes_view, name='admin-classes'),
    path('add-class/', views.add_class_view, name='add-class'),
    path('delete-class/<int:id>/', views.delete_class_view, name='delete-class'),
    path('add-subject/<int:class_id>/', views.add_subject_view, name='add-subject'),
    path('get-subjects/', views.get_subjects_by_class, name='get-subjects'),
    # exam and tests
    path('assessments/', views.assessments_view, name='assessments'),
    path('add-exam/', views.add_exam_view, name='add-exam'),
    path('add-test/', views.add_test_view, name='add-test'),
    path('edit-exam/<int:id>/', views.edit_exam_view, name='edit-exam'),  # Path for editing an exam
    path('edit-test/<int:id>/', views.edit_test_view, name='edit-test'),  # Path for editing a test
    path('delete-exam/<int:id>/', views.delete_exam_view, name='delete-exam'),  # Path for deleting an exam
    path('delete-test/<int:id>/', views.delete_test_view, name='delete-test'), 
    #  results
    path('exam-results/', views.exam_results_view, name='exam-results'),
    path('marked-students-tests/', views.admin_marked_students_tests_view, name='admin_marked_students_tests'), 
    path('admin-edit-marks/<int:mark_id>/', views.admin_edit_marks_view, name='admin_edit_marks'),
    path('admin-edit-exam-marks/<int:mark_id>/', views.admin_edit_exam_marks_view, name='admin_edit_exam_marks'),
    path('configurations/', views.configurations_view, name='configurations'),
    path('generate-pdf/<int:mark_id>/', views.generate_pdf, name='generate_pdf'),
    path('generate-exam-pdf/<int:mark_id>/', views.generate_exam_pdf, name='generate_exam_pdf'),
    path('print-tests-folder/<str:class_name>/', views.print_tests_folder, name='print_tests_folder'),
    path('print-exams-folder/<str:class_name>/', views.print_exams_folder, name='print_exams_folder'),

    # fees tracking
    path('student-fees/', views.student_fees_view, name='student-fees'),
    path('manage-payment/<int:student_id>/', views.manage_payment_view, name='manage_payment'),
    path('view-payments/<int:student_id>/', views.view_payments_view, name='view_payments'),
    path('edit-payment/<int:payment_id>/', views.edit_payment_view, name='edit_payment'),
    path('manage-academic-years/', views.manage_academic_years_view, name='manage_academic_years'),
    path('manage-terms/<int:year_id>/', views.manage_terms_view, name='manage_terms'),
    path('enroll-students/<int:year_id>/<int:term_id>/', views.enroll_students_view, name='enroll_students'),
    path('unenroll/<int:enrollment_id>/', views.unenroll_student, name='unenroll_student'),
    path('delete-academic-year/<int:year_id>/', views.delete_academic_year_view, name='delete_academic_year'),
    path('delete-term/<int:term_id>/', views.delete_term_view, name='delete_term'),
    path('get-students-by-class/<int:class_id>/', views.get_students_by_class, name='get_students_by_class'),
    path('get-enrollments/<int:year_id>/<int:term_id>/', views.get_enrollments_view, name='get_enrollments'),
    path('fees-records/', views.fees_records_view, name='fees_records'),
    path('fees-records/balances/', views.fetch_balances, name='fetch_balances'),
    path('fees-records/balances/pdf/', views.generate_balances_pdf, name='generate_balances_pdf'),
    path('fees-records/summary-pdf/', views.generate_summary_pdf, name='generate_summary_pdf'),

 
]
