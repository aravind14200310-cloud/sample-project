@echo off
cd /d "C:\Users\ELCOT\Desktop\New folder\Expense"
echo Running Django checks...
.\apk\Scripts\python.exe manage.py check
echo.
echo Collecting static files...
.\apk\Scripts\python.exe manage.py collectstatic --noinput
echo.
echo Running dev server...
.\apk\Scripts\python.exe manage.py runserver 0.0.0.0:8000
