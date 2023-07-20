# THMMY Bot

A discord utility bot used in the Electrical and Computer Engineering - AUTH student's discord server (not officially affiliated with the university). It utilizes a PostgreSQL database to provide schedule and professor information to the members, while also providing some server-specific utilities to the admins.  
Note that all the messages sent by the bot that are meant to be viewed by non-admin server members are written in the server's main language, greek.
# Table of contents



- [Commands](#commands)
    - [info](#info)    
    - [now](#now)    
    - [update](#update)    
- [Schedule Importer](#schedule-importer)

  

# Commands

The default command prefix for this bot is "meli"
</br></br>



## info

**Command syntax**  
  
> meli info <professor's last name in greek>  

**Command description**  
  
  Sends information about a specific professor (e.g. email, office location, website).
 
 **Command output**  
   
<img src="https://github.com/gselivanof/ecebot/blob/main/README_ASSETS/info.png" width="300" >
</br>

**Database requirements**  
  
This command requires a table named "professors" with the following structure:  
  
| simple_last_name (VARCHAR)  | sector (VARCHAR) | last_name (VARCHAR) | first_name (VARCHAR) | email (VARCHAR) | office (VARCHAR) | phone (VARCHAR) | website (VARCHAR) | img_url (VARCHAR) |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| παπαδοπουλος  | Electronics and Computer Engineering  | Παπαδόπουλος  | Γεώργιος  | email@auth.gr  | Building x, Floor y  | 0000000000  | examplesite.auth.gr  | image.jpg  |








## now

**Command syntax**  
  
> meli now <optional year number (1-5) 

**Command description**  
  
  Sends information about all lessons that are currently taking place. If a year is specified, it also sends the upcoming lesson (if it exists).
 
 **Command output (No year specified)**  
   
<img src="https://github.com/gselivanof/ecebot/blob/main/README_ASSETS/now.png" width="300" >
</br>


**Database requirements**  
  
This command requires a table for each year named "schedule_yearx", where x is the number of year (1-5), with the following structure:  
  
| lesson_name (VARCHAR) | location (VARCHAR) | day (VARCHAR) | start_time (VARCHAR) | end_time (VARCHAR)|
| ------------- | ------------- | ------------- | ------------- | ------------- |
| Calculus I  | Amphitheater of Polytechnic School  | Monday  | 18:00  | 20:00  |







## update
**Command syntax**  

> meli update 

**Command description** 

  Updates the members' year specific roles by increasing the year by 1 (e.g. Year 1 --> Year 2). Maximum value is Year 5.
  
**Command usage**  
    The server has a role for each year ("Year 1" up to "Year 5") that each member selects when first entering the server. This command is meant to be executed once at the beggining of each academic year so that the members don't have to manually select a new role. After each command execution, a pastebin link with a log of the changes is sent back.
    
   
# Schedule Importer

**Description**

In order to not add every lesson manually, we use the html schedule provided by https://classschedule.auth.gr/#/ and import it into the database using schedule_importer.py.

**Usage**

- A schedule.html file must be in the same directory as schedule_importer.py. 
- Modifying the 'year' variable in the python script lets us select which year's schedule we want to import 
- Uncommenting the line that executes the TRUNCATE commands allows for removal of all rows from the table before importing the lessons. 

Note that the script automatically creates a table named "schedule_yearx", where x is the number of year (1-5), if it does not already exist.
