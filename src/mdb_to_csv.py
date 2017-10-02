# read mdb tables and convert to csv
from sys import argv
import subprocess
import csv

mdb_file = argv[1]

table_names = subprocess.Popen(['mdb-tables', '-1', mdb_file], stdout=subprocess.PIPE).communicate()[0]
tables = table_names.split('\n')

for table in tables:
	if table != '':
		filename = table.replace(' ','_') + '.csv'
		file = open(filename, 'w')
		print "Dumping " + table
		contents = subprocess.Popen(["mdb-export", mdb_file, table], stdout=subprocess.PIPE).communicate()[0]
		file.write(contents)
		file.close()
