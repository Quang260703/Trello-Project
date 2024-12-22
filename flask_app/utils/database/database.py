import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow

class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = '127.0.0.1'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'
        self.tables         = ['boards', 'users', 'cards', 'user_board']
        
        # NEW IN HW 3-----------------------------------------------------------------
        self.encryption     =  {   'oneway': {'salt' : b'averysaltysailortookalongwalkoffashortbridge',
                                                 'n' : int(pow(2,5)),
                                                 'r' : 9,
                                                 'p' : 1
                                             },
                                'reversible': { 'key' : '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='}
                                }
        #-----------------------------------------------------------------------------

    def query(self, query = "SELECT * FROM users", parameters = None):

        cnx = mysql.connector.connect(host     = self.host,
                                      user     = self.user,
                                      password = self.password,
                                      port     = self.port,
                                      database = self.database,
                                      charset  = 'latin1'
                                     )


        if parameters is not None:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row

    def createTables(self, purge=False, data_path = 'flask_app/database/'):
        ''' FILL ME IN WITH CODE THAT CREATES YOUR DATABASE TABLES.'''

        #should be in order or creation - this matters if you are using forign keys.
         
        if purge:
            for table in self.tables[::-1]:
                self.query(f"""DROP TABLE IF EXISTS {table}""")
            
        # Execute all SQL queries in the /database/create_tables directory.
        for table in self.tables:
            
            #Create each table using the .sql file in /database/create_tables directory.
            with open(data_path + f"create_tables/{table}.sql") as read_file:
                create_statement = read_file.read()
            self.query(create_statement)

            # Import the initial data
            try:
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=','):
                    params.append(row)
            
                # Insert the data
                cols = params[0]; params = params[1:] 
                self.insertRows(table = table,  columns = cols, parameters = params)
            except:
                print('no initial data')

    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
        
        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)
        keys, values      = ','.join(columns), ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO {table} ({keys}) VALUES """
        if has_multiple_rows:
            for p in parameters:
                query += f"""({values}),"""
            query     = query[:-1] 
            parameters = list(itertools.chain(*parameters))
        else:
            query += f"""({values}) """                      
        
        insert_id = self.query(query,parameters)[0]['LAST_INSERT_ID()']         
        return insert_id
    
    # return a nested dict that hierarchically represents the complete data for a board
    def getBoardData(self, id=0):
        board = {}
        lists = ["to_do", "doing", "completed"]
        list_id = 0
        for item in lists:
            cards = self.query(f"SELECT * FROM cards WHERE board_id = {id} AND list_id = {list_id} ORDER BY position ASC")
            board[item] = {
                'cards': {}
            }
            for card in cards:
                card_id = card['card_id']
                board[item]['cards'][card_id] = {
                    'name': card.get('name', 'NULL'),
                    'description': card.get('description', 'NULL')
                }
            list_id += 1
        return board
    
    # create a card
    def createCard(self, board_id=0, list_id=0, name='name', description='description'):
        try:
            select_query = "SELECT COUNT(*) AS card_count FROM cards WHERE board_id = %s AND list_id = %s"
            select_parameters = (board_id, list_id)
            count = self.query(select_query, select_parameters)
            if count and len(count) > 0:
                position = count[0]['card_count']
            else:
                position = 0
            insert_query = "INSERT INTO cards (board_id, list_id, position, name, description) VALUES (%s, %s, %s, %s, %s)"
            insert_parameters = (board_id, list_id, position, name, description)
            id = self.query(insert_query, insert_parameters)[0]['LAST_INSERT_ID()']  
            return {'success': id}
        except Exception as e:
            return {'fail': 'Insert card fail'}
    
    # update a list
    def updateList(self, board_id=0, list_id=0):
        try:
            select_query = "SELECT card_id FROM cards WHERE board_id = %s AND list_id = %s ORDER BY position"
            select_parameters = (board_id, list_id)
            cards = self.query(select_query, select_parameters)

            update_query = "UPDATE cards SET position = CASE "
            update_parameters = []
        
            for index, card in enumerate(cards):
                update_query += "WHEN card_id = %s THEN %s "
                update_parameters.append(card['card_id'])
                update_parameters.append(index)
        
            # Complete the query with a WHERE clause to update only the specific board and list
            update_query += "END WHERE board_id = %s AND list_id = %s"
            update_parameters.extend([board_id, list_id])

            # Execute the batch update
            self.query(update_query, tuple(update_parameters))
            
            return {'success': 'Cards updated by position successfully'}
        except Exception as e:
            return {'fail': 'Update list fail'}

    # update a card 
    def updateCard(self, card_id=0, name='name', description='description'):
        try:
            update_query = "UPDATE cards SET name = %s, description = %s WHERE card_id = %s"
            parameters = (name, description, card_id)
            self.query(update_query, parameters)

            return {'success': 'Card updated successfully'}
        except Exception as e:
            return {'fail': 'Update card fail'}
    
    # delete a card
    def deleteCard(self, card_id=0, board_id=0):
        try:
            query = "SELECT list_id FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            id = self.query(query, parameters)[0]['list_id']

            update_query = "DELETE FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            self.query(update_query, parameters)

            self.updateList(board_id, id)
            return {'success': 'Card deleted successfully'}
        except Exception as e:
            return {'fail': 'Delete card fail'}
    
    # moving card to a different list
    def movingCardDifferentList(self, board_id=0, list_id=0, card_id=0, position=0):
        try:
            update_query = "UPDATE cards SET position = position + 1 WHERE board_id = %s AND list_id = %s AND position >= %s"
            parameters = (board_id, list_id, position)
            self.query(update_query, parameters)

            update_card_query = "UPDATE cards SET position = %s, list_id = %s WHERE card_id = %s"
            parameters = (position, list_id, card_id)
            self.query(update_card_query, parameters)

            return {'success': 'Card positions updated successfully'}
        except Exception as e:
            return {'fail': 'Moving card fail'}
    
    # get position
    def getPosition(self, card_id=0):
        try:
            query = "SELECT position FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            return self.query(query, parameters)[0]['position']
        except Exception as e:
            return {'fail': 'Moving card fail'}

    # get list id  
    def getListId(self, card_id=0):
        try:
            query = "SELECT list_id FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            return self.query(query, parameters)[0]['list_id']
        except Exception as e:
            return {'fail': 'Moving card fail'}

    #moving card position down
    def movingCardDown(self, board_id=0, list_id=0, card_id=0, position=0):
        try:
            query = "SELECT position FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            old_position = self.query(query, parameters)[0]['position']

            print(old_position)
            update_query = "UPDATE cards SET position = position - 1 WHERE board_id = %s AND list_id = %s AND position > %s AND position <= %s"
            parameters = (board_id, list_id, old_position, position)
            self.query(update_query, parameters)

            update_query = "UPDATE cards SET position = %s, list_id = %s WHERE card_id = %s"
            parameters = (position, list_id, card_id)
            self.query(update_query, parameters)

            return {'success': 'Card removed and positions updated successfully'}
        except Exception as e:
            return {'fail': 'Remove card fail'}
    
    # moving card position up
    def movingCardUp(self, board_id=0, list_id=0, card_id=0, position=0):
        try:
            query = "SELECT position FROM cards WHERE card_id = %s"
            parameters = (card_id,)
            old_position = self.query(query, parameters)[0]['position']

            update_query = "UPDATE cards SET position = position + 1 WHERE board_id = %s AND list_id = %s AND position < %s AND position >= %s"
            parameters = (board_id, list_id, old_position, position)
            self.query(update_query, parameters)

            update_query = "UPDATE cards SET position = %s, list_id = %s WHERE card_id = %s"
            parameters = (position, list_id, card_id)
            self.query(update_query, parameters)

            return {'success': 'Card removed and positions updated successfully'}
        except Exception as e:
            return {'fail': 'Remove card fail'}
    
    # create a new board
    def createBoard(self, name='name', users=[]):
        try:
            user_list = ', '.join(f"'{email}'" for email in users)
            query = f"SELECT user_id FROM users WHERE email IN ({user_list})"
            ids = self.query(query)
            user_ids = [item['user_id'] for item in ids]
            board_query = "INSERT INTO boards (name) VALUES (%s)"
            board_id = self.query(board_query, (name,))[0]['LAST_INSERT_ID()']  

            parameters = [[board_id, user_id] for user_id in user_ids]
            self.insertRows('user_board', ['board_id', 'user_id'], parameters)

            return {'success': board_id}
        except Exception as e:
            return {'fail': 'Created board fail'}

    # check if user in db
    def checkUser(self, email='email'):
        try:
            query = "SELECT * FROM users WHERE email = %s"
            user_list = self.query(query, (email,))
            if len(user_list) == 0:
                return {'fail': 'No accounts found'}
            return {'success': user_list[0]['user_id']}
        except Exception as e:
            return {'fail': 'No accounts found'}
    
    # get all boards for email
    def getAllBoards(self, email='email'):
        try:
            query = "SELECT user_id FROM users WHERE email = %s"
            user_list = self.query(query, (email,))
            query = "SELECT board_id FROM user_board WHERE user_id = %s"
            board_list = self.query(query, (user_list[0]['user_id'],))
            if len(board_list) == 0:
                return {'fail': 'No board found'}
            board_id_list = []
            board_name_list = []
            for board in board_list:
                query = "SELECT name FROM boards WHERE board_id = %s"
                board_name_list.append(self.query(query, (board['board_id'],))[0]['name'])
                board_id_list.append(board['board_id'])
            return {'success': {
                        'id': board_id_list,
                        'name': board_name_list
                    }}
        except Exception as e:
            return {'fail': 'No board found'}
    
    # get name of board from id
    def getBoardName(self, id=0):
        try:
            query = "SELECT name FROM boards WHERE board_id = %s"
            names = self.query(query, (id,))
            return names[0]['name']
        except Exception as e:
            return {'fail': 'No board found'}


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
    # create an user
    def createUser(self, email='me@email.com', password='password'):
        try:
            query = "SELECT * FROM users WHERE email = %s"
            email_list = self.query(query, (email,))
            if len(email_list) > 0:
                return {'fail': 'This email already exists'}
            encrypted_password = self.onewayEncrypt(password)
            query = "INSERT INTO users (email, password) VALUES (%s, %s)"
            parameters = (email, encrypted_password)
            self.query(query, parameters)
            return {'success': 'Create account successful'}
        except Exception as e:
            return {'fail': 'Create account fail'}

    # Check if an user is in database
    def authenticate(self, email='me@email.com', password='password'):
        try:
            encrypted_password = self.onewayEncrypt(password)
            parameters = (email, encrypted_password)
            query = "SELECT * FROM users WHERE email = %s and password = %s"
            user_list = self.query(query, parameters)
            if len(user_list) == 0:
                return {'fail': 'Check your email or password'}
            return {'success': 'Authenticate successful'}
        except Exception as e:
            return {'fail': 'Authenticate fail'}

    # one way encryption for password
    def onewayEncrypt(self, string):
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt = self.encryption['oneway']['salt'],
                                          n    = self.encryption['oneway']['n'],
                                          r    = self.encryption['oneway']['r'],
                                          p    = self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string

    # Encrypt that can be reversed
    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])
        
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message