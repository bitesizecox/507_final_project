Getting Started:

Final_Project folder should contain:
- final_project.py
- fp_test.py
- requirements.txt
- data (folder)
	- college_tuition.csv
	- median_income.csv
	- us_postal_codes.csv

In your terminal, navigate to the directory that this folder is stored. 
To run the file, enter "python3 final_project.py" in your command line and press enter.


Prerequisites:

Must install all modules listed in requirements.txt.
	- Create and activate a virtual environment
	- Run: pip install -r requirements.txt in your shell

Must have Google API key to process data. Instructions for obtaining this key can be found at: https://developers.google.com/+/web/api/rest/oauth


Running Tests:

fp_test.py has a number of test cases to ensure that the program is running properly in a number of ways:
	- tests the initialization of the database
	- tests the navigation and joins of the database tables
	- tests program output given various combination of commands

In order to run this file, simply enter "python3 fp_test.py" in your command line.


Built With:

This program utilizes the following sources:
	- Wikipedia
	- Google Places API
	- Plot.ly