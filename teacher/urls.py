from django.urls import path
from teacher import views
from django.contrib.auth.views import LoginView

urlpatterns = [
path('teacherclick', views.teacherclick_view),
path('teacherlogin', LoginView.as_view(template_name='teacher/teacherlogin.html'),name='teacherlogin'),
path('teachersignup', views.teacher_signup_view,name='teachersignup'),
path('teacher-dashboard', views.teacher_dashboard_view,name='teacher-dashboard'),
path('teacher-exam', views.teacher_exam_view,name='teacher-exam'),
path('teacher-add-exam', views.teacher_add_exam_view,name='teacher-add-exam'),
path('teacher-view-exam', views.teacher_view_exam_view,name='teacher-view-exam'),
path('delete-exam/<int:pk>', views.delete_exam_view,name='delete-exam'),


path('teacher-question', views.teacher_question_view,name='teacher-question'),
path('teacher-add-question', views.teacher_add_question_view,name='teacher-add-question'),
path('teacher-view-question', views.teacher_view_question_view,name='teacher-view-question'),
path('see-question/<int:pk>', views.see_question_view,name='see-question'),
path('remove-question/<int:pk>', views.remove_question_view,name='remove-question'),
# classes
path('teacher-classes', views.teacher_classes_view, name='teacher-classes'),
path('add-marks/<int:student_id>/', views.add_marks_view, name='add_marks'),
path('add-test-marks/<int:student_id>/', views.add_test_marks_view, name='add_test_marks'),
path('load_subjects/', views.load_subjects, name='load-subjects'),
path('marked-students/', views.marked_students_view, name='marked-students'),
path('marked-students-tests/', views.marked_students_tests_view, name='marked-students-tests'),
path('delete-mark/<int:mark_id>/', views.delete_mark_view, name='delete-mark'),
path('edit-marks/<int:mark_id>/', views.edit_marks_view, name='edit-marks'),
path('load-test-subjects/', views.load_test_subjects, name='load-test-subjects'),
path('delete-all-marks/<str:class_name>/', views.delete_all_marks_view, name='delete-all-marks'),
path('delete-class-marks/<str:class_name>/', views.delete_class_marks_view, name='delete-class-marks'),
]