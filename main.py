import AngryLion
import sys
import os
import colors
import shutil

def listFiles(dir):
	rootdir = dir
	for root, subFolders, files in os.walk(rootdir, topdown=False):
		for file in files:
			yield os.path.join(root,file)
	return
	
# replaces "key" with "value" in file
def replace_content(file, key, value):
	newfile = open(file+".tmp",'w')
	oldfile = open(file)
	
	# replace all the keys with their value
	for line in oldfile:
		newfile.write(line.replace(key, value));
		
	newfile.close()
	oldfile.close()
	
	# remove original file and rename tmp file
	os.remove(file)
	shutil.move(file+".tmp", file)

def header():
	art = """
              ___    ___   __._____  ___   __.__    __  ____. ___   __ 
             /   \  |    \|  |  __  \   \/  /|  |  |  |/ __  \    \|  |
            /  \  \ |  |\    |   /  / \    / |  |__|  |   /  |  |\    |
           /__/ \__\|__|  \__|__|\__\  |__|  |_____|__|\_____|__|  \__|
                   """

	sys.stderr.write(colors.bold() + colors.fg('cyan') + art + colors.end() + "\n\n")

# create our angylion object and set the xml
lion = AngryLion.AngryLion()
if not lion.setConfigXML(file('./config.xml').read()):
	print ""
	print "fix the above errors in the xml"
	sys.exit(-1)

# get the supported templates
templates = lion.parseTemplates()

# print our fancy header 
header()

# now we ask the user which one he/she wants to create
print ""
print "Please select the template you want to create:\n"
for template in templates:
	print "  * %s: %s" % (template, templates[template])
print ""

valid = False

# ask the user for his choice, until he chose a valid option
while not valid:
	choice = raw_input("Your choice: ")
	# check if the choice is available
	for template in templates:
		if choice == template:
			valid = True
			
	if not valid:
		print "Choice not valid, try again..."
		
# set the template in our angrylion object
lion.setCurrentTemplate(choice)

# we parse all keys that are user input and ask the user for it
keys = lion.parseInputs(lion.getKeyTags("input"))
values = {}

print ""
for key in keys:
	valid = False
	while not valid:
		input = raw_input(keys[key])
		if not input == "":
			values[key] = input
			valid = True
print ""

# parse the folders of the given template
folders = lion.parseFolders()

# get the switch statements inside the config
switches = lion.parseSwitch("input")

if switches:
	for switch in switches:
		valid = False
		while not valid:
			# parse the case statements
			cases = lion.parseCase(switch)
			# print the prompt statement for the user
			print "%s [%s]:" % (switches[switch], ', '.join(cases))
			choice_case = raw_input()
			
			try:
				cases.index(choice_case)
				valid = True
			except ValueError:
				pass
				
		lion.resolveCase(switch, choice_case)
			
# all user keys are available
# we let the angrylion finish all other keys
lion.makeKeys(values)

if not os.path.exists("./workspace"):
	os.makedirs("./workspace")

# clean the workspace folder
print "Cleaning the workspace folder..."
shutil.rmtree('./workspace/')

# copy those folders to the workspace
print "Copying template folders to workspace..."
for folder in folders:
	shutil.copytree("./"+str(lion.keys['(template_folder)'])+"/"+str(folder), "./workspace/"+lion.keys[folders[folder]])
	
for folder in folders:
	current_folder = str(lion.keys[folders[folder]])
	print "Renaming files and replacing keys in ./workspace/" + current_folder
	
	for file in listFiles("./workspace/"+current_folder):
		newfile = str(file)
		for key in lion.keys:
			replace_content(file, str(key), str(lion.keys[key]))
			newfile = newfile.replace(str(key), str(lion.keys[key]))
	
		os.rename(str(file), newfile)
		
print ""
print "Your template files are inside the 'workspace' folder, copy them wher you need them."
	
