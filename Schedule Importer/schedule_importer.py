import pandas as pd
import math
import psycopg2

#Target database credentials
db_host = 'host'
db_name = 'name'
db_pass = 'password'
db_user = 'username'

#Connect to the database
con = psycopg2.connect(dbname=db_name,user=db_user,password=db_pass, host=db_host)
cur = con.cursor() 

#Reading the html schedule file (downloaded from https://classschedule.auth.gr/#/)
table_MN = pd.read_html('schedule.html')

#
#   CHANGE THE year VARIABLE TO THE DESIRABLE VALUE (1-5)
#

year = 1

#Selecting the table that corresponds to the desirable year
df = table_MN[year - 1]



names = []

#A class for lesson entries in the db
class Lesson:
    name = 'N/A'
    room  = 'N/A'
    start_time = 'N/A'
    end_time = 'N/A'
    day_name = 'N/A'

    def __del__(self):
         print ("deleted lesson")

    def __key(self):
        return (self.name, self.room, self.start_time,self.end_time,self.day_name)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Lesson):
            return self.__key() == other.__key()
        return NotImplemented

#The list that we add the Lesson objects so that we can import them to the database later
Lesson_list = []

#Day names as written in the schedule html file
Day_names = ['Δευτέρα','Τρίτη','Τετάρτη','Πέμπτη','Παρασκευή']


for index, row in df.iterrows():
  
    for day in Day_names:

        #Index to keep track of current info type being read from table
        index = 0
        #Storing the information of the lesson currently being read
        LessonInfo = ['','','','']
        #Last character read from table
        lastch = ' '
        
        #To know when we first read a numeric character
        firstnum = True

        #To keep track of parenthesis
        parenthesis = False

        #If there is a lesson
        if isinstance(row[day], str):
                #We read every character in the line and detect different infromation
                for ch in row[day]:
                    if( ch == '('): 
                        parenthesis = True
                    if( ch == ')'): 
                        parenthesis = False
                    
                    if 902<= ord(ch) <= 939: ##CAPITAL GREEK
                        if lastch != ' ' and ch != 'Ι' and parenthesis!= True: #These creteria are matched when the capital letter in NOT part of the lesson name
                            
                            if 48<= ord(lastch) <= 57:
                                #If the lastch was a number and the current ch is a capital letter
                                #it means have moved on from a previous lesson into a new one without moving
                                #a table cell (happens when there are more than 1 lesson at a given time)

                                #We save the previous lesson to the Lesson_list and we reset index and firstnum
                                newLesson = Lesson()
                                newLesson.name = LessonInfo[0]
                                newLesson.room = LessonInfo[1]
                                newLesson.start_time = LessonInfo[2]
                                newLesson.end_time = LessonInfo[3]
                                newLesson.day_name = day
                                Lesson_list.append(newLesson)
                                del newLesson
                                LessonInfo = ['','','','']
                                index = 0
                                firstnum = True
                            else:
                                #This means the capital letter is part of the classroom's name
                                index = 1                       
                            LessonInfo[index] += ch
                        else:
                            #Capital letter is part of the lesson name
                            LessonInfo[index] += ch

                    elif 940<= ord(ch) <= 974: ##LOWERCASE GREEK
                        LessonInfo[index] += ch     

                    elif 48<= ord(ch) <= 57: ##NUMBER
                        if firstnum:    #If it's the first numerical character we switch the index to 2 (start_time)
                            index = 2
                            firstnum = False
                        LessonInfo[index] += ch

                    elif ch == '-': 
                        if lastch == ' ': #Only happens before the lesson's end time appearence in the table
                            index = 3
                        else:
                            LessonInfo[index] += ch
                    elif ch == ' ':

                        if index != 3: #If it is not the space character right after the - used to seperate the start and end times
                            LessonInfo[index] += ch
                    else:

                        LessonInfo[index] += ch
                    
                    lastch = ch

                #We save the collected info into a Lesson object
                newLesson = Lesson()
                newLesson.name = LessonInfo[0]
                newLesson.room = LessonInfo[1]
                newLesson.start_time = LessonInfo[2]
                newLesson.end_time = LessonInfo[3]
                newLesson.day_name = day
                #We add the lesson object to the Lesson_list
                Lesson_list.append(newLesson)
                #We delete the object to move on
                del newLesson
                #We reset the index and the LessonInfo
                index = 0
                LessonInfo = ['','','','']


Lesson_list = list(set(Lesson_list))

#Checks if the table for the specified year's schedule exists and if it does not creates its
cur.execute("select exists(select * from information_schema.tables where table_name='schedule_year"+str(year)+"');")
if cur.fetchone()[0] == False:
    print("Table not found: Creating...")
    cur.execute("CREATE TABLE schedule_year"+str(year)+"(lesson_name VARCHAR(255), location VARCHAR(50),day VARCHAR(20),start_time VARCHAR(6), end_time VARCHAR(6));")

#
#       UNCOMMENT THE LINE BELOW IF YOU WANT TO EMPTY THE DB TABLE BEFORE ADDING THE LESSONS TO THE DATABASE
#
#cur.execute("TRUNCATE TABLE schedule_year"+str(year)+";")


#Add the lesson entries into the database
for x in Lesson_list:
            command = "INSERT INTO schedule_year"+str(year)+" VALUES ('{}','{}','{}','{}','{}');".format(x.name,x.room,x.day_name,x.start_time,x.end_time)
            print(command)
            cur.execute(command)
            con.commit()   

con.close()