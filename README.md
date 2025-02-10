# School Grading, Report Card, and Fees Tracking System 
![developer](https://img.shields.io/badge/Developed%20By%20%3A-Sumit%20Kumar-red)
---
## screenshots
### Homepage
![homepage snap](https://github.com/Liven-Allan/Sch_Management_System/tree/main/static/screenshots/homepage.png?raw=true)
### Admin Dashboard
![dashboard snap](https://github.com/Liven-Allan/Sch_Management_System/tree/main/static/screenshots/adminhomepage.png?raw=true)
### Exam and Test Assessment 
![doctor snap](https://github.com/Liven-Allan/Sch_Management_System/tree/main/static/screenshots/exam.png?raw=true)
### Teacher
![doctor snap](https://github.com/Liven-Allan/Sch_Management_System/tree/main/static/screenshots/teacher.png?raw=true)
---
## Functions
### Admin
- Create Admin account using command
```
py manage.py createsuperuser
```
- After Login, can see Total Number Of Student, Teacher.
- Can View, Add, Delete, Teacher.
- Can View, Add, Delete Student.
- Can See Student Marks (Exam Marks and Test Marks).
- Can Add, View, Delete Exam or Test Record

### Teacher
- Registered teachers by the admin can only login once given credentials.
- After Login, can see only students of a particular class which was selected during registering of a teacher.
- Can Add, View, Delete Exam or Test marks for individual students.

## HOW TO RUN THIS PROJECT
- Install Python(3.7.6) (Dont Forget to Tick Add to Path while installing Python)
- Open Terminal and Execute Following Commands :
```
python -m pip install -r requirements. txt
```
- Download This Project Zip Folder and Extract it
- Move to project folder in Terminal. Then run following Commands :
```
py manage.py makemigrations
py manage.py migrate
py manage.py runserver
```
- Now enter following URL in Your Browser Installed On Your Pc
```
http://127.0.0.1:8000/
```

## CHANGES REQUIRED FOR CONTACT US PAGE
- In settins.py file, You have to give your email and password
```
EMAIL_HOST_USER = 'youremail@gmail.com'
EMAIL_HOST_PASSWORD = 'your email password'
EMAIL_RECEIVING_USER = 'youremail@gmail.com'
```
