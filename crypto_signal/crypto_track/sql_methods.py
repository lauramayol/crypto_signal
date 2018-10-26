
import psycopg2 as mc
import os


class SqlCommands():

    def __init__(self, host, user, db):
        self.host = host
        self.user = user
        self.db = db

    def db_connect(self):
        mydb = mc.connect(
            host=self.host,
            user=self.user,
            password=os.environ.get("RDS_PASSWORD"),
            database=self.db
        )
        return mydb

    def select_results(self, db_object, filter_statement=""):
        '''
            Variables:
            db_object (str) = table or view to be selected FROM
            filter_statement (str) = suffix to follow after the FROM statement (usually WHERE clause).

            Return Value:
            Returns a list for all items found in db_object
        '''
        my_select = self.sql_shell("SELECT * FROM", db_object, filter_statement)
        return my_select

    def sql_shell(self, action, db_object, suffix=""):
        '''
            Executes mySQL statement as per action variable.

            Variables:
            action (str) = can be SELECT * FROM, TRUNCATE, CALL, DROP TABLE...
            object (str) = specify the table name or stored procedure
            suffix (str) = can be WHERE statement or ending parenthesis (for CALL statement) as needed.

            Return Value:
            Returns a list of values when action is SELECT.
        '''
        mydb = self.db_connect()
        mycursor = mydb.cursor()
        action_format = action.upper()

        statement = f"{action_format} {db_object}{suffix}"

        try:
            mycursor.execute(statement)

            if action_format[:6] == "SELECT":
                myresult = mycursor.fetchall()
                _list = []
                for x in myresult:
                    #_list_from_return = list(x)
                    _list.append(x)
                return _list
            else:
                mydb.commit()

        except Exception as exc:
            print(exc)
        else:
            print(f"'{statement}' has been executed.")

        finally:
            mycursor.close()

            mydb.close()

    def exec_statement(self, action, db_object):
        '''
            Variables:
            action (str) = can be TRUNCATE, CALL, DROP TABLE...
            object (str) = specify the table name or stored procedure
        '''
        self.sql_shell(action, db_object)

    def data_insert(self, db_object, db_object_tuple, data_list):
        '''
            Recieves a db_object that must be a table and inserts records from data_list.

            Variables:
            db_object (str) = table to INSERT into
            db_object_tuple (tuple) = tuple of headers that will match final table.
            data_list (list) = list of tuples representing each record to be inserted into the table. Order of data must match the order of db_object_tuple.

        '''
        mydb = self.db_connect()
        mycursor = mydb.cursor()

        header_tuple = self.create_insert_tuple(db_object_tuple, "%s")

        insert_statement = f"INSERT INTO {db_object} {header_tuple[0]} VALUES {header_tuple[1]}"

        try:

            mycursor.executemany(insert_statement, data_list)

            mydb.commit()
        except Exception as exc:
            print(exc)
        finally:
            mycursor.close()
            mydb.close()

    def create_insert_tuple(self, header_tuple, delimeter):
        '''
            Creates text that will be used to insert data into table.

            Variables:
            header_tuple (tuple) = tuple of headers that will match final table.
            delimeter (str) = delimeter that will populate placeholder for insert VALUE.

            Return Value:
            Returns a tuple of two strings. First one will be used to specify the headers within INSERT statement, and the second will be used to populate placeholder string.
        '''
        header_str = self.pre_create_tuple(header_tuple, True)
        value_str = self.pre_create_tuple(header_tuple, False, delimeter)

        return (header_str, value_str)

    def pre_create_tuple(self, t, is_header, delim=""):
        '''
            Iterates through the header tuple to create text that will be used to insert data into table.

            Variables:
            t (tuple) = tuple of headers to iterate
            is_header (bool) = True if we need to populate headers, False if we need to create a string of delimeters.
            delim (str) = optional delimeter.

            Return Value:
            Returns a string of values inside of parenthesis to be used as part of INSERT statements.
        '''
        formatted_str = "("
        for i in t:
            if is_header:
                pre = i
            else:
                pre = delim
            formatted_str += pre + ", "

        formatted_str += ")"
        # remove final commas
        return_value = formatted_str.replace(", )", ")")

        return return_value
