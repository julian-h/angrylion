## @package AngryLion
#  This module supplies the AngryLion class
#

from bs4 import BeautifulSoup

import logging
import string
import shutil
import uuid
import sys
import os
import re

## AngryLion documentation
#
#  AngryLion is a class that supports methods to work with the config file
#  it can parse different elements and resolves some keys based on input values
#
class AngryLion():
	## The constructor.
	def __init__(self):
		# the beautiful soup object
		self.soup = None
		self.xmldata = ""
		self.current_template = ""
		
		# all supported key types are defined here
		# the first value is the string that is put into the 'type=""' attribute
		# the second value is the handler function for this type
		self.key_types = {'value' : getattr(self, 'makeValues'), 
						  'uuid' : getattr(self, 'makeUUID'),
						  'lowercase' : getattr(self, 'makeLower'),
						  'uppercase' : getattr(self, 'makeUpper'),
						  'replace' : getattr(self, 'makeReplace'),
						  'escape' : getattr(self, 'makeEscape'),
						  'concatenate' : getattr(self, 'makeConcat')}
		
		# create a logger
		self.logger = logging.getLogger('angrylion')
		handler = logging.FileHandler('./angrylion.log')
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)
		self.logger.setLevel(logging.DEBUG)
		
		# input keys
		self.input_keys = {}
		
		# all folders
		self.folders = {}
		
		# all keys
		self.keys = {}
		
	## Method to check if the given XML is valid or not
	#
	#  @param self The object pointer
	#  @param xmldata A string containing the config XML
	#
	#  @return True if the xml is valid
	#
	def checkXML(self, xmldata):
		valid = True
		soup = BeautifulSoup(xmldata)
		
		# the tag name and the attributes that this tag requires
		checks = {'template' : ['name', 'desc'],
				  'folder' : ['name', 'rename'],
				  'key' : ['name', 'type'],
				  'switch' : ['name', 'type'],
				  'case' : ['name']}
		
		# check the attributes each tag MUST have
		for check in checks:
			tags = soup.findAll(check)
			attrs = checks[check]
			
			for tag in tags:
				for attr in attrs:
					if not tag.has_key(attr):
						print "tag: '" + check + "' is missing the attribute: '" + attr + "'"
						valid = False
						
		# now check the key types specific attributes
		types = {'replace' : ['format', 'match', 'replacement'],
				 'escape' : ['format', 'char'],
				 'input' : ['prompt'],
				 'value' : ['value'],
				 'switch' : ['value'],
				 'concatenate' : ['format'],
				 'uppercase' : ['format']}
		
		for type in types:
			tags = soup.findAll('key', {'type' : type})
			attrs = types[type]
			
			for tag in tags:
				for attr in attrs:
					if not tag.has_key(attr):
						print "key tag with name: '" + tag['name'] + "' is missing the attribute: '" + attr + "'"
						valid = False
		
		
		return valid
		
		
	## Method to set the xmldata for later use
	#
	#  @param self The object pointer
	#  @param xmldata A string containing the XML
	#
	#  @return True on success, False when the xml data is not valid
	#
	def setConfigXML(self, xmldata):
		if (self.checkXML(xmldata)):
			self.xmldata = xmldata
		else:
			return False
		
		# create the soup object which will be used later
		self.soup = BeautifulSoup(xmldata)
		return True
		
	## Method to set the current template we are working on
	#
	#  @param self The object pointer
	#  @param template The name of the template to use
	#
	def setCurrentTemplate(self, template):
		self.current_template = template
	
	## Method to parse all key tags of a given type in a given template
	#
	#  @param self The object pointer.
	#  @param type Name of the type we want to extract
	#
	#  @return A list which contains the full tags
	#	
	def getKeyTags(self, type):
		base_tag = self.soup.find("template", {"name" : self.current_template})
		key_tags = base_tag.findAll("key", { "type" : type})
		
		return key_tags
	
	## Method to get a list of available templates with the corresponding description 
	#
	#  @param self The object pointer.
	#
	#  @return dictionary with the template name as identifier and the description as value
	#
	def parseTemplates(self):
		templateTags = self.soup('template')
		
		templates = {}
		
		for template in templateTags:
			try:
				templates[template['name']] = template['desc']
			except KeyError:
				msg = "template: '" + template['name'] + "' doesn't have an attribute 'desc'"
				self.log(msg, "ERROR")
		
		return templates

	## Method to parse a switch tag
	#
	#  @param self The object pointer.
	#  @param type Type of the switch tag
	#
	#  @return A dictionary, with the name of the switch tag as identifier and the prompt value as description
	#
	def parseSwitch(self, type):
		base_tag = self.soup.find("template", {"name" : self.current_template})
		switch_tags = base_tag.findAll("switch", {"type" : type})
		
		data = {}
		for switch in switch_tags:
			try:
				data[switch['name']] = switch['prompt']
			except KeyError:
				msg = "switch tag: '" + switch['name'] + "' doesn't have an attribute 'prompt'"
				self.log(msg, "ERROR")
		
		return data
		
	## Method to parse the case statements of a given switch tag
	#
	#  @param self The object pointer.
	#  @param switch The name of the switch statement
	#
	#  @return A list of case options
	#
	def parseCase(self, switch):
		base_tag = self.soup.find("template", {"name" : self.current_template})
		switch_tag = base_tag.find("switch", {"name" : switch})
		case_tags = switch_tag.findAll("case")
		
		list = []
		for case_tag in case_tags:
			try:
				list.append(case_tag['name'])
			except KeyError:
				msg = "case tag doesn't have an attribute 'name'"
				self.log(msg, "ERROR")
				
		return list
	
	## Method to parse the folder tags in the xml and return a dictionary of those tags
	#
	#  @param self The object pointer.
	#
	#  @return A dictionary with the name of the folder as identifier and the rename value as description
	#
	def parseFolders(self):
		base_tag = self.soup.find("template", {"name" : self.current_template})
		folder_tags = base_tag.findAll("folder")
		
		for folder in folder_tags:
			try:
				self.folders[folder['name']] = folder['rename']
			except KeyError:
				msg = "folder tag: '" + folder['name'] + "' doesn't have an attribute 'rename'"
				self.log(msg, "ERROR")
				
		return self.folders
		
	## Method to parse a key tag (or a list of tags) of type "input"
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier
	#
	#  @return A dictionary with the name of the key as identifier and the 'prompt' value as description
	#
	def parseInputs(self, key_tags):
		data = {}
		# iterate over all key tags and store them for later use
		for key_tag in key_tags:
			try:
				data[key_tag['name']] = key_tag['prompt']
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'prompt'"
				self.log(msg, "ERROR")
		
		return data
		
	## Method to parse a key tag (or a list of tags) of type "value"
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier
	#
	#  @return A dictionary with the name of the key as identifier and the 'value' value as description
	#
	def makeValues(self, key_tags):		
		data = {}
		for key_tag in key_tags:
			try:
				data[key_tag['name']] = key_tag['value']
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'value'"
				self.log(msg, "ERROR")
			
		return data
		
	## Method to handle a tag (or tags) from type "escape", this will escape the character in the 'char' attribute
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier
	#
	#  @return A dictionary with the name of the key as identiefier and the escaped string as description
	#
	def makeEscape(self, key_tags):
		data = {}
		for key_tag in key_tags:
			# get the format string
			try:
				format_str = self.fillFormatStr(key_tag['format'])
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'format'"
				self.log(msg, "ERROR")
			
			# now we escape the specified char
			try:
				data[key_tag['name']] = format_str.replace(key_tag['char'], "\\"+key_tag['char'])
			except KeyError:
				msg = "the key '" + key_tag['name'] + "' doesn't contain an attribute 'char'"
				self.log(msg, "ERROR")
		
		return data
		
	## Method to handle a tag (or tags) from type "uppercase", this will convert the string to uppercase
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier 
	#
	#  @return A dictionary with the name of the key as identiefier and the uppercase string as description 
	#
	def makeUpper(self, key_tags):
		data = {}
		for key_tag in key_tags:
			# get the format string
			try:
				format_str = self.fillFormatStr(key_tag['format'])
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'format'"
				self.log(msg, "ERROR")
			
			# convert the string to uppercase
			data[key_tag['name']] = format_str.upper()
		
		return data
	
	## Method to handle a tag (or tags) from type "lowercase", this will convert the string to lowercase
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier 
	#
	#  @return A dictionary with the name of the key as identiefier and the lowercase string as description 
	#
	def makeLower(self, key_tags):
		data = {}
		for key_tag in key_tags:
			# get the format string
			try:
				format_str = self.fillFormatStr(key_tag['format'])
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'format'"
				self.log(msg, "ERROR")
			
			# convert the string to lowercase
			data[key_tag['name']] = format_str.lower()
		
		return data
		
	## Method to handle a tag (or tags) from type "concatenate", this will create a string based on a format string
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier 
	#
	#  @return A dictionary with the name of the key as identiefier and the concatenated string as description 
	#
	def makeConcat(self, key_tags):
		data = {}
		# check in every key tag, if all of the dependencies (in the format string, are available)
		for key_tag in key_tags:
			try:
				format_str = self.fillFormatStr(key_tag['format'])
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have an attribute 'format'"
				self.log(msg, "ERROR")
		
			data[key_tag['name']] = format_str
		
		return data
		
	## Method to handle a tag (or tags) from type "uuid", this will create a random UUID for each key
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier 
	#
	#  @return A dictionary with the name of the key as identiefier and the uuid as description 
	#
	def makeUUID(self, key_tags):
		uuids = {}
		for key_tag in key_tags:
			try:
				uuids[key_tag['name']] = str(uuid.uuid4())
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' is not accessible"
				self.log(msg, "ERROR")
				
		return uuids
		
	## Method to handle a tag (or tags) from type "replace", this will replace a given character in a given string with the new char
	#
	#  @param self The object pointer.
	#  @param key_tags A dictionary which has the tags attribute names as the identifier 
	#
	#  @return A dictionary with the name of the key as identiefier and the replaced string as description 
	#
	def makeReplace(self, key_tags):
		data = {}
		for key_tag in key_tags:
			try:
				format_str = self.fillFormatStr(key_tag['format'])
				format_str = format_str.replace(key_tag['match'], key_tag['replacement'])
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' doesn't have attribute 'format' or 'match' or 'replacement'"
				self.log(msg, "ERROR")
				
			data[key_tag['name']] = format_str
				
		return data
	
	## Method to generate all other keys that are not user input
	#
	#  @param self The object pointer.
	#  @param input_values Dictionary of all user keys and their values
	#
	def makeKeys(self, input_values):
		self.keys = dict(self.keys, **input_values)
		
		# iterate over all key types and call their handler function
		for key_type in self.key_types:
			data_keys = self.key_types[key_type](self.getKeyTags(key_type))
			if data_keys:
				self.keys = dict(self.keys, **data_keys)
		
	## Method to fill a given format string with the values
	#
	#  @param self The object pointer.
	#  @param format_str The format string where we want to insert the values (e.g. '$((bfp_name))' this will be replaced with the value of the key: '(bfp_name)')
	# 
	#  @return The string filled with all values
	#
	def fillFormatStr(self, format_str):
		symbols = re.findall(r"\$\(([()a-z_]*)\)", format_str)
		for symbol in symbols:
			# check if the symbol is available
			try:
				self.keys[symbol]
			except KeyError:
				if not self.resolveSymbol(symbol):
					msg = "key '" + symbol + "' could not be resolved"
					self.log(msg, "CRITICAL")
		
			# if we get here, the symbol should be available and this call cannot fail
			format_str = format_str.replace("$("+symbol+")", str(self.keys[symbol]))
		
		# return our filled string
		return format_str
		
	## Method to resolve a switch case statement inside the XML
	#
	#  @param self The object pointer.
	#  @param switch The name of the switch statement
	#  @param case The name of the case statement
	#
	def resolveCase(self, switch, case):
		base_tag = self.soup.find("template", {"name" : self.current_template})
		switch_tag = base_tag.find("switch", {"name" : switch})
		case_tag = switch_tag.find("case", {"name" : case})
		key_tags = case_tag.findAll("key")
		
		for key_tag in key_tags:
			try:
				self.keys[key_tag['name']] = key_tag['value']
			except KeyError:
				msg = "key tag: '" + key_tag['name'] + "' has no attribute 'value'"
				self.log(msg, "ERROR")
		
	## Method to resolve missing symbols
	#
	#  @param self The object pointer.
	#  @param symbol The symbol that needs to be resolved
	#
	#  @return True on succuess
	#
	def resolveSymbol(self, symbol):
		# get the key tag with the name that we need to resolve
		base_tag = self.soup.find("template", {"name" : self.current_template})
		key_tag = base_tag.find("key", { "name" : symbol})
		
		# check if the key tag is present
		if key_tag == None:
			# there is no key tag, something is wrong with the XML
			return False
			
		try:
			# call the handler function of the key type
			data = self.key_types[key_tag['type']]([key_tag])
		except KeyError:
			# if the key type is not supported we return false
			return False
					
		# add the new key to the intern list
		self.keys = dict(self.keys, **data)
		
		return True
		
	## Method to log a message of a given level to the logfile
	#
	#  @param self The object pointer.
	#  @param msg Message to log
	#  @param level Logging level
	#
	def log(self, msg, level):
		if level == "ERROR":
			self.logger.error(msg)
			print "Error, exiting, see log for more info"
			sys.exit(-1)
		elif level == "WARN":
			self.logger.warn(msg)
		elif level == "INFO":
			self.logger.info(msg)
		elif level == "DEBUG":
			self.logger.debug(msg)
		elif level == "CRITICAL":
			self.logger.critical(msg)
			print "Critical error, exiting, see log for more info"
			sys.exit(-1)