#!/usr/bin/perl

# Einbinden von Module
use CGI;
use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use IO::Socket::INET;
use LWP::Simple;
use Net::Ping;


print "Content-type: text/html\n\n";

# Konfig auslesen
my %pcfg;
my %miniservers;
tie %pcfg, "Config::Simple", "$lbpconfigdir/pluginconfig.cfg";
$UDP_Port = %pcfg{'MAIN.UDP_Port'};
#$UDP_Send_Enable = %pcfg{'MAIN.UDP_Send_Enable'};
$HTTP_TEXT_Send_Enable = %pcfg{'MAIN.HTTP_TEXT_Send_Enable'};
$MINISERVER = %pcfg{'MAIN.MINISERVER'};
my $SHOWALL = %pcfg{'MAIN.SHOW_ALL_Enable'};
%miniservers = LoxBerry::System::get_miniservers();


# Miniserver konfig auslesen
#print "\n".substr($MINISERVER, 10, length($MINISERVER))."\n";
$i = substr($MINISERVER, 10, length($MINISERVER));
$LOX_Name = $miniservers{$i}{Name};
$LOX_IP = $miniservers{$i}{IPAddress};
$LOX_User = $miniservers{$i}{Admin};
$LOX_PW = $miniservers{$i}{Pass};

#print "Miniserver\@".$LOX_Name."<br>";
#print $LOX_IP."<br>";
#print $LOX_User."<br>";
#print $LOX_PW."<br>";

# Mit dieser Konstruktion lesen wir uns alle POST-Parameter in den Namespace R.
my $cgi = CGI->new;
$cgi->import_names('R');
# Ab jetzt kann beispielsweise ein POST-Parameter 'form' ausgelesen werden mit $R::form.


# POST request
$NUT_Name = $R::name;


# Wenn keine POST, dann alle Magic Home Controller abfragen
if($NUT_Name eq ""){
	# NUT USP Name 
	$NUT_Name = "ups";
	# print "Leer<br>";
} 
LOGDEB "NUT USV Name: $NUT_Name";
	


# Create my logging object
my $log = LoxBerry::Log->new ( 
	name => 'cronjob',
	filename => "$lbplogdir/nut.log",
	append => 1
	);
LOGSTART "NUT-Server cronjob start";

# UDP-Port Erstellen für Loxone
my $sock = new IO::Socket::INET(PeerAddr => $LOX_IP,
                PeerPort => $UDP_Port,
                Proto => 'udp', Timeout => 1) or die('Error opening socket.');
			

# Loxone HA-Miniserver by Marcel Zoller	
if($LOX_Name eq "lxZoller1"){
	# Loxone Minisever ping test
	LOGOK " Loxone Zoller HA-Miniserver";
	#$LOX_IP="172.16.200.7"; #Testvariable
	#$LOX_IP='172.16.200.6'; #Testvariable
	$p = Net::Ping->new();
	$p->port_number("80");
	if ($p->ping($LOX_IP,2)) {
				LOGOK "Ping Loxone: Miniserver1 is online.";
				LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
			} else{ 
				LOGALERT "Ping Loxone: Miniserver1 not online!";
				LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
				
				$p = Net::Ping->new();
				$p->port_number("80");
				$LOX_IP = $miniservers{2}{IPAddress};
				$LOX_User = $miniservers{2}{Admin};
				$LOX_PW = $miniservers{2}{Pass};
				#$LOX_IP="172.16.200.6"; #Testvariable
				if ($p->ping($LOX_IP,2)) {
					LOGOK "Ping Loxone: Miniserver2 is online.";
					LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				} else {
					LOGALERT "Ping Loxone: Miniserver2 not online!";
					LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
					#Failback Variablen !!!
					$LOX_IP = $miniservers{1}{IPAddress};
					$LOX_User = $miniservers{1}{Admin};
					$LOX_PW = $miniservers{1}{Pass};	
				} 
			}
		$p->close();			
}

my @words;
my $filename = 'upsstatus.log';
system ("echo leer>upsstatus.log");

system ("upsc $NUT_Name@localhost>$filename 2>&1");

# open file
open(my $fh, '<:encoding(UTF-8)', $filename)
	or die "Could not open file '$filename' $!";

	
# Ausgabe aller Magic Home Device	
while (my $row = <$fh>) {
  chomp $row;
  $loc = index($row, "Init SSL");
  # print "$loc\n";
  if($loc==-1){

	# Possible values for status_set:
	# ups.status  
	#
	# OL = 10 - On line (mains is present)
	# OB = 20 - On battery (mains is not present)
	# LB = 1 - Low battery
	# HB = 2 - High battery
	# RB = 3 - The battery needs to be replaced
	# CHRG = 4 - The battery is charging
	# DISCHRG = 5 - The battery is discharging (inverter is providing load power) BYPASS - UPS bypass circuit is active - no battery protection is available CAL - UPS is currently performing runtime calibration (on battery)
	# OFF =6 - UPS is offline and is not supplying power to the load
	# OVER = 7 - UPS is overloaded
	# TRIM = 8 - UPS is trimming incoming voltage (called "buck" in some hardware) BOOST - UPS is boosting incoming voltage
	# FSD = 9 - Forced Shutdown (restricted use, see the note below)
	
	if(index($row, "ups.status")!=-1){
	
		$status_id = 0;
		if(index($row, "OL")!=-1){$status_id =10;}
		if(index($row, "OB")!=-1){$status_id =20;}
		if(index($row, "LB")!=-1){$status_id +=1;}
		if(index($row, "HB")!=-1){$status_id +=2;}
		if(index($row, "RB")!=-1){$status_id +=3;}
		if(index($row, "DISCHRG")!=-1){$status_id +=5;}
		elsif(index($row, "CHRG")!=-1){$status_id +=4;}
		if(index($row, "OFF")!=-1){$status_id +=6;}
		if(index($row, "OVER")!=-1){$status_id +=7;}
		if(index($row, "TRIM")!=-1){$status_id +=8;}
		if(index($row, "FSD")!=-1){$status_id +=9;}
		
		
		
		print "ups.status.id\@$status_id<br>";

	}
	elsif(index($row, "battery.runtime: ")!=-1){
		#print "$row<br>";
		$row_runtime = $row;
		@words = split(/: /, $row_runtime,2);
		# print "Word 1: $words[0]<br>";
		# print "Word 2: $words[1]<br>";
		$str_min = ($words[1])/60;
		
		print "battery.runtime.min\@$str_min<br>";

	}
	
	
	$row =~ s/: /@/ig;
	
	
	if($SHOWALL==0){
		# print "SHOW ALL: disable<br>";
		if(index($row, "battery.charge@")!=-1){print "$row<br>";}
		if(index($row, "battery.temperature@")!=-1){print "$row<br>";}
		if(index($row, "battery.voltage@")!=-1){print "$row<br>";}
		if(index($row, "input.voltage@")!=-1){print "$row<br>";}
		if(index($row, "output.voltage@")!=-1){print "$row<br>";}
		if(index($row, "output.frequency@")!=-1){print "$row<br>";}
		if(index($row, "ups.status@")!=-1){print "$row<br>";}
		if(index($row, "ups.load@")!=-1){print "$row<br>";}
		
		
	 }else
	 {
		print "$row<br>";	
	 }
	}
  }

# We start the log. It will print and store some metadata like time, version numbers
# LOGSTART "V-ZUG cronjob start";
  
# Now we really log, ascending from lowest to highest:
# LOGDEB "This is debugging";                 # Loglevel 7
# LOGINF "Infos in your log";                 # Loglevel 6
# LOGOK "Everything is OK";                   # Loglevel 5
# LOGWARN "Hmmm, seems to be a Warning";      # Loglevel 4
# LOGERR "Error, that's not good";            # Loglevel 3
# LOGCRIT "Critical, no fun";                 # Loglevel 2
# LOGALERT "Alert, ring ring!";               # Loglevel 1
# LOGEMERGE "Emergency, for really really hard issues";   # Loglevel 0
  
LOGEND "Operation finished sucessfully.";
