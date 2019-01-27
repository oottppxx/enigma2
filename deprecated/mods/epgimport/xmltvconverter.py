import time
import calendar
import log
#from pprint import pprint
from xml.etree.cElementTree import ElementTree, Element, SubElement, tostring, iterparse

# %Y%m%d%H%M%S
def quickptime(str):
	return time.struct_time((int(str[0:4]), int(str[4:6]), int(str[6:8]),
				 int(str[8:10]), int(str[10:12]), 0,
				 -1, -1, 0))


def get_time_utc(timestring, fdateparse):
	#print "get_time_utc", timestring, format
	try:
		values = timestring.split(' ')
		tm = fdateparse(values[0])
		timegm = calendar.timegm(tm)
		#suppose file says +0300 => that means we have to substract 3 hours from localtime to get gmt
		timegm -= (3600*int(values[1])/100)
		return timegm
	except Exception, e:
		print "[XMLTVConverter] get_time_utc error:", e
		return 0

# Preferred language should be configurable, but for now,
# we just like Dutch better!
def get_xml_string(elem, name):
	r = ''
	try:
		for node in elem.findall(name):
			txt = node.text
			lang = node.get('lang', None)
			if not r:
				r = txt
			elif lang == "nl":
				r = txt
	except Exception,  e:
		print "[XMLTVConverter] get_xml_string error:",  e
	# Now returning UTF-8 by default, the epgdat/oudeis must be adjusted to make this work.
	return r.encode('utf-8')

def enumerateProgrammes(fp):
	"""Enumerates programme ElementTree nodes from file object 'fp'"""
	for event, elem in iterparse(fp):
		if elem.tag == 'programme':
			yield elem
			elem.clear()
		elif elem.tag == 'channel':
			# Throw away channel elements, save memory
			elem.clear()


class XMLTVConverter:
	def __init__(self, channels_dict, category_dict, dateformat = '%Y%m%d%H%M%S %Z'):
	    self.channels = channels_dict
	    self.categories = category_dict
	    if dateformat.startswith('%Y%m%d%H%M%S'):
		    self.dateParser = quickptime
	    else:
		    self.dateParser = lambda x: time.strptime(x, dateformat)

	def enumFile(self, fileobj):
		print>>log, "[XMLTVConverter] Enumerating event information"
		lastUnknown = None
		# there is nothing no enumerate if there are no channels loaded
		if not self.channels:
			return
		for elem in enumerateProgrammes(fileobj):
			channel = elem.get('channel')
			channel = channel.lower()
			if not channel in self.channels:
				if lastUnknown!=channel:
					print>>log, "Unknown channel: ", channel
					lastUnknown=channel
				# return a None object to give up time to the reactor.
				yield None
				continue
			try:
				services = self.channels[channel]
				start = get_time_utc(elem.get('start'), self.dateParser)
				stop = get_time_utc(elem.get('stop'), self.dateParser)
				title = get_xml_string(elem, 'title')
                                try:
				  subtitle = get_xml_string(elem, 'sub-title')
                                except:
                                  subtitle = ''
                                try:
				  description = get_xml_string(elem, 'desc')
                                except:
                                  description = ''
				category = get_xml_string(elem, 'category')
				cat_nr = self.get_category(category,  stop-start)
				# data_tuple = (data.start, data.duration, data.title, data.short_description, data.long_description, data.type)
				if not stop or not start or (stop <= start):
					print "[XMLTVConverter] Bad start/stop time: %s (%s) - %s (%s) [%s]" % (elem.get('start'), start, elem.get('stop'), stop, title)
				yield (services, (start, stop-start, title, subtitle, description, cat_nr))
			except Exception,  e:
				print "[XMLTVConverter] parsing event error:", e

	def get_category(self,  str,  duration):
		if (not str) or (type(str) != type('str')):
			return 0
		if str in self.categories:
			category = self.categories[str]
			if len(category) > 1:
				if duration > 60*category[1]:
					return category[0]
			elif len(category) > 0:
				return category
		return 0
