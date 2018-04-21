import unittest
from final_project import *

class TestDatabase(unittest.TestCase):

    def test_school_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT Name FROM Colleges'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Pennsylvania College of Technology',), result_list)
        self.assertEqual(len(result_list), 4040)

        sql = '''
            SELECT Name, Type, Status, StateAbbr
            FROM Colleges
            WHERE Type="Less than 2-year"
            ORDER BY Tuition DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 60)
        self.assertEqual(result_list[2][3], 'MI')

        conn.close()

    def test_states_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT StateName
            FROM StatesIncome
            WHERE StateAbbr="MI"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][0], "Michigan")

        sql = '''
            SELECT StateAbbr
            FROM StatesIncome
            ORDER BY StateName DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 51)
        self.assertEqual(result_list[2][0], "WV")

        conn.close()

    def test_cities_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT CityName, State
            FROM Cities
            WHERE CityName="New Haven"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 38)
        self.assertEqual(result_list[33][1], "Indiana")


    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Name
            FROM Colleges
                JOIN StatesIncome
                ON Colleges.StateId=StatesIncome.Id
            WHERE Colleges.StateAbbr="SC"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('University of South Carolina-Beaufort',), result_list)
        conn.close()

class TestCollegeSearch(unittest.TestCase):

    def test_college_search(self):
        results = process_command('state=mi orderby=bottom')
        self.assertEqual(results[1][0], 'Washtenaw Community College')

        results = process_command('orderby=bottom sortby=private')
        self.assertEqual(results[5][1], '2-year')

        results = process_command('price_range=between price_low=8000 price_high=15000 state=MA')
        self.assertEqual(results[7][0], "Massachusetts College of Art and Design")

        results = process_command('sortby=other orderby=top limit=5')
        self.assertEqual(results[0][3], 'California')


class TestFunctions(unittest.TestCase):

    def test_functions_search(self):
        results = process_command('view_job_opps')
        self.assertEqual(results, False)

        results = process_command('clear_history=search')
        self.assertTrue(results, True)

        results = process_command('cart=view')
        self.assertEqual(results, False)


unittest.main()