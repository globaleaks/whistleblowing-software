#!/usr/bin/python
# Copyright 2007 Johannes Renner and Mike Perry. See LICENSE file.

import struct
import socket
import TorCtl
import StatsSupport

from TorUtil import plog
try:
  import GeoIP
  # GeoIP data object: choose database here
  geoip = GeoIP.new(GeoIP.GEOIP_STANDARD)
  #geoip = GeoIP.open("./GeoLiteCity.dat", GeoIP.GEOIP_STANDARD)
except:
  plog("NOTICE", "No GeoIP library. GeoIPSupport.py will not work correctly")
  # XXX: How do we bail entirely..  


class Continent:
  """ Continent class: The group attribute is to partition the continents
      in groups, to determine the number of ocean crossings """
  def __init__(self, continent_code):
    self.code = continent_code 
    self.group = None
    self.countries = []

  def contains(self, country_code):
    return country_code in self.countries

# Set countries to continents
africa = Continent("AF")
africa.group = 1
africa.countries = ["AO","BF","BI","BJ","BV","BW","CD","CF","CG","CI","CM",
   "CV","DJ","DZ","EG","EH","ER","ET","GA","GH","GM","GN","GQ","GW","HM","KE",
   "KM","LR","LS","LY","MA","MG","ML","MR","MU","MW","MZ","NA","NE","NG","RE",
   "RW","SC","SD","SH","SL","SN","SO","ST","SZ","TD","TF","TG","TN","TZ","UG",
   "YT","ZA","ZM","ZR","ZW"]

asia = Continent("AS")
asia.group = 1
asia.countries = ["AP","AE","AF","AM","AZ","BD","BH","BN","BT","CC","CN","CX",
   "CY","GE","HK","ID","IL","IN","IO","IQ","IR","JO","JP","KG","KH","KP","KR",
   "KW","KZ","LA","LB","LK","MM","MN","MO","MV","MY","NP","OM","PH","PK","PS",
   "QA","RU","SA","SG","SY","TH","TJ","TM","TP","TR","TW","UZ","VN","YE"]

europe = Continent("EU")
europe.group = 1
europe.countries = ["EU","AD","AL","AT","BA","BE","BG","BY","CH","CZ","DE",
   "DK","EE","ES","FI","FO","FR","FX","GB","GI","GR","HR","HU","IE","IS","IT",
   "LI","LT","LU","LV","MC","MD","MK","MT","NL","NO","PL","PT","RO","SE","SI",
   "SJ","SK","SM","UA","VA","YU"]

oceania = Continent("OC")
oceania.group = 2
oceania.countries = ["AS","AU","CK","FJ","FM","GU","KI","MH","MP","NC","NF",
   "NR","NU","NZ","PF","PG","PN","PW","SB","TK","TO","TV","UM","VU","WF","WS"]

north_america = Continent("NA")
north_america.group = 0
north_america.countries = ["CA","MX","US"]

south_america = Continent("SA")
south_america.group = 0
south_america.countries = ["AG","AI","AN","AR","AW","BB","BM","BO","BR","BS",
   "BZ","CL","CO","CR","CU","DM","DO","EC","FK","GD","GF","GL","GP","GS","GT",
   "GY","HN","HT","JM","KN","KY","LC","MQ","MS","NI","PA","PE","PM","PR","PY",
   "SA","SR","SV","TC","TT","UY","VC","VE","VG","VI"]

# List of continents
continents = [africa, asia, europe, north_america, oceania, south_america]

def get_continent(country_code):
  """ Perform country -- continent mapping """
  for c in continents:
    if c.contains(country_code):
      return c
  plog("INFO", country_code + " is not on any continent")
  return None

def get_country(ip):
  """ Get the country via the library """
  return geoip.country_code_by_addr(ip)

def get_country_from_record(ip):
  """ Get the country code out of a GeoLiteCity record (not used) """
  record = geoip.record_by_addr(ip)
  if record != None:
    return record['country_code']

class GeoIPRouter(TorCtl.Router):
  # TODO: Its really shitty that this has to be a TorCtl.Router
  # and can't be a StatsRouter..
  """ Router class extended to GeoIP """
  def __init__(self, router):
    self.__dict__ = router.__dict__
    self.country_code = get_country(self.get_ip_dotted())
    if self.country_code != None: 
      c = get_continent(self.country_code)
      if c != None:
        self.continent = c.code
        self.cont_group = c.group
    else: 
      plog("INFO", self.nickname + ": Country code not found")
      self.continent = None
   
  def get_ip_dotted(self):
    """ Convert long int back to dotted quad string """
    return socket.inet_ntoa(struct.pack('>I', self.ip))

class GeoIPConfig:
  """ Class to configure GeoIP-based path building """
  def __init__(self, unique_countries=None, continent_crossings=4,
     ocean_crossings=None, entry_country=None, middle_country=None,
     exit_country=None, excludes=None):
    # TODO: Somehow ensure validity of a configuration:
    #   - continent_crossings >= ocean_crossings
    #   - unique_countries=False --> continent_crossings!=None
    #   - echelon? set entry_country to source and exit_country to None

    # Do not use a country twice in a route 
    # [True --> unique, False --> same or None --> pass] 
    self.unique_countries = unique_countries
    
    # Configure max continent crossings in one path 
    # [integer number 0-n or None --> ContinentJumper/UniqueContinent]
    self.continent_crossings = continent_crossings
    self.ocean_crossings = ocean_crossings
 
    # Try to find an exit node in the destination country
    # use exit_country as backup, if country cannot not be found
    self.echelon = False

    # Specify countries for positions [single country code or None]
    self.entry_country = entry_country
    self.middle_country = middle_country
    self.exit_country = exit_country

    # List of countries not to use in routes 
    # [(empty) list of country codes or None]
    self.excludes = excludes
