@ECHO off

start /min python manage.py runserver
timeout /t 10 /nobreak

start /min npm run sch_system
