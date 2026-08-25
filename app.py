# =====================================================================
# ΕΥΡΕΣΗ ΠΛΗΣΙΕΣΤΕΡΟΥ ΣΧΟΛΕΙΟΥ - Web εφαρμογή (Streamlit)
# Βάση δεδομένων: 209 Δημόσια Δημοτικά Σχολεία της Δ/νσης Π.Ε. Α' Αθήνας
# (επίσημος πίνακας 2024-2025, με ακριβείς διευθύνσεις)
# =====================================================================
import re
import json
import time
import difflib
import unicodedata

import requests
import streamlit as st
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium

# ---------------------------------------------------------------------
geolocator = Nominatim(user_agent="teacher-closest-school-finder-webapp (contact: example@example.com)")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ATTICA_BBOX = (37.75, 23.45, 38.25, 24.05)  # south, west, north, east

# ---------------------------------------------------------------------
# ΕΝΣΩΜΑΤΩΜΕΝΗ ΒΑΣΗ ΣΧΟΛΕΙΩΝ (Δ/νση Π.Ε. Α' Αθήνας, 2024-2025)
# Κάθε εγγραφή: name (επίσημη ονομασία), street, postcode, area
# ---------------------------------------------------------------------
SCHOOLS_JSON = """[{"name":"1ο Δημοτικό Σχολείο Αθηνών","street":"ΣΠΥΡΟΥ ΜΕΡΚΟΥΡΗ 20","postcode":"11634","area":"ΠΑΓΚΡΑΤΙ"},{"name":"2ο Δημοτικό Σχολείο Αθηνών","street":"ΔΑΜΑΡΕΩΣ 65","postcode":"11633","area":"ΠΑΓΚΡΑΤΙ"},{"name":"3ο Δημοτικό Σχολείο Αθηνών","street":"ΕΜΠΕΔΟΚΛΕΟΥΣ 12","postcode":"11636","area":"ΠΑΓΚΡΑΤΙ"},{"name":"4ο Δημοτικό Σχολείο Αθηνών","street":"ΚΟΝΩΝΟΣ & ΘΕΑΓΕΝΟΥΣ","postcode":"11634","area":"ΠΑΓΚΡΑΤΙ"},{"name":"8ο Δημοτικό Σχολείο Αθηνών","street":"ΠΟΝΤΟΥ & ΑΓ.ΘΩΜΑ","postcode":"11527","area":"ΓΟΥΔΗ"},{"name":"9ο Δημοτικό Σχολείο Αθηνών","street":"ΕΥΦΡΟΝΙΟΥ 81 & ΜΠΙΓΛΙΣΤΑΣ 2","postcode":"16121","area":"ΚΑΡΑΒΕΛ"},{"name":"10ο Δημοτικό Σχολείο Αθηνών","street":"ΖΑΓΟΡΑΣ 18","postcode":"11527","area":"ΑΜΠΕΛΟΚΗΠΟΙ"},{"name":"11ο Δημοτικό Σχολείο Αθηνών","street":"ΠΑΠΑΝΑΣΤΑΣΙΟΥ & ΚΟΡΑΚΑ 44","postcode":"10445","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"12ο Δημοτικό Σχολείο Αθηνών","street":"ΚΟΡΓΙΑΛΕΝΙΟΥ 2","postcode":"11526","area":"ΕΡΥΘΡΟΣ ΣΤΑΥΡΟΣ"},{"name":"13ο Δημοτικό Σχολείο Αθηνών","street":"ΣΤΙΛΠΩΝΟΣ 38","postcode":"11636","area":"ΜΕΤΣ"},{"name":"14ο Δημοτικό Σχολείο Αθηνών","street":"ΣΙΝΑ 70","postcode":"10672","area":"ΛΥΚΑΒΗΤΤΟΣ"},{"name":"15ο Δημοτικό Σχολείο Αθηνών","street":"ΠΑΝΑΓΗ ΚΥΡΙΑΚΟΥ 10","postcode":"11152","area":"ΚΟΛΩΝΑΚΙ"},{"name":"16ο Δημοτικό Σχολείο Αθηνών","street":"ΤΙΜΟΛΕΟΝΤΟΣ ΦΙΛΗΜΟΝΟΣ 19","postcode":"11521","area":"ΑΜΠΕΛΟΚΗΠΟΙ"},{"name":"17ο Δημοτικό Σχολείο Αθηνών","street":"ΑΜΠΕΛΑΚΙΩΝ 24","postcode":"11522","area":"ΑΜΠΕΛΟΚΗΠΟΙ"},{"name":"18ο Δημοτικό Σχολείο Αθηνών","street":"ΑΧΑΪΑΣ 3","postcode":"11523","area":"ΑΜΠΕΛΟΚΗΠΟΙ"},{"name":"20ο Δημοτικό Σχολείο Αθηνών","street":"ΜΑΥΡΟΓΕΝΟΥΣ 8","postcode":"11251","area":"ΑΓ. ΠΑΝΤΕΛΕΗΜΟΝΑΣ"},{"name":"21ο Δημοτικό Σχολείο Αθηνών","street":"ΚΥΠΡΟΥ 43","postcode":"11253","area":"ΠΛ. ΑΜΕΡΙΚΗΣ"},{"name":"22ο Δημοτικό Σχολείο Αθηνών","street":"ΛΕΥΚΩΣΙΑΣ 50","postcode":"11253","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"23ο Δημοτικό Σχολείο Αθηνών","street":"ΜΙΧΑΗΛ ΝΟΜΙΚΟΥ 26","postcode":"11253","area":"ΠΑΤΗΣΙΑ"},{"name":"24ο Δημοτικό Σχολείο Αθηνών","street":"ΣΑΡΑΝΤΑΠΟΡΟΥ 20","postcode":"11144","area":"Α. ΠΑΤΗΣΙΑ"},{"name":"25ο Δημοτικό Σχολείο Αθηνών","street":"ΠΑΝΔΟΣΙΑΣ 2","postcode":"11142","area":"ΛΑΜΠΡΙΝΗ"},{"name":"26ο Δημοτικό Σχολείο Αθηνών","street":"ΦΩΚ. ΝΕΓΡΗ 63","postcode":"11361","area":"ΚΥΨΕΛΗ"},{"name":"27ο Δημοτικό Σχολείο Αθηνών","street":"ΧΙΛΙΑΝΔΑΡΙΟΥ 2","postcode":"11363","area":"ΚΥΨΕΛΗ"},{"name":"28ο Δημοτικό Σχολείο Αθηνών","street":"ΜΟΥΣΤΟΞΥΔΗ 23","postcode":"11473","area":"ΣΧ. ΕΥΕΛΠΙΔΩΝ"},{"name":"29ο Δημοτικό Σχολείο Αθηνών","street":"ΔΟΙΡΑΝΗΣ 43","postcode":"11363","area":"ΝΕΑ ΚΥΨΕΛΗ"},{"name":"30ο Δημοτικό Σχολείο Αθηνών","street":"ΧΙΛΙΑΝΔΑΡΙΟΥ 2","postcode":"11363","area":"ΚΥΨΕΛΗ"},{"name":"31ο Δημοτικό Σχολείο Αθηνών","street":"ΖΥΜΠΡΑΚΑΚΗ 47 & ΖΕΡΒΟΥΔΑΚΗ","postcode":"10445","area":"ΚΑΤΩ ΠΑΤΗΣΙΑ"},{"name":"32ο Δημοτικό Σχολείο Αθηνών","street":"ΑΡΙΣΤΟΤΕΛΟΥΣ 55","postcode":"10433","area":"ΠΛ. ΒΙΚΤΩΡΙΑΣ"},{"name":"33ο Δημοτικό Σχολείο Αθηνών","street":"ΕΥΑΓΡΙΟΥ & ΚΡΟΥΣΙΟΥ","postcode":"11363","area":"Α. ΚΥΨΕΛΗ"},{"name":"34ο Δημοτικό Σχολείο Αθηνών","street":"ΔΙΟΠΟΛΕΩΣ & ΣΙΝΟΠΟΥΛΟΥ","postcode":"11142","area":"ΡΙΖΟΥΠΟΛΗ"},{"name":"35ο Δημοτικό Σχολείο Αθηνών","street":"ΚΩΛΕΤΤΗ 34","postcode":"10682","area":"ΕΞΑΡΧΕΙΑ"},{"name":"36ο Δημοτικό Σχολείο Αθηνών","street":"ΙΟΥΣΤΙΝΙΑΝΟΥ 30-34","postcode":"11473","area":"ΕΞΑΡΧΕΙΑ"},{"name":"38ο Δημοτικό Σχολείο Αθηνών","street":"ΚΟΚΚΕΡΕΛ 14","postcode":"11146","area":"Α. ΚΥΨΕΛΗ"},{"name":"39ο Δημοτικό Σχολείο Αθηνών","street":"ΑΧΑΡΝΩΝ 399","postcode":"11143","area":"ΑΓ. ΕΛΕΥΘΕΡΙΟΣ"},{"name":"40ο Δημοτικό Σχολείο Αθηνών","street":"ΜΟΜΦΕΡΑΤΟΥ & ΦΑΛΗΡΕΩΣ 2-4","postcode":"11475","area":"ΓΚΥΖΗ"},{"name":"41ο Δημοτικό Σχολείο Αθηνών","street":"ΒΑΡΒΑΚΗ 23","postcode":"11474","area":"ΓΚΥΖΗ"},{"name":"44ο Δημοτικό Σχολείο Αθηνών","street":"ΜΗΛΙΑΡΑΚΗ 57-59","postcode":"11145","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"45ο Δημοτικό Σχολείο Αθηνών","street":"ΠΥΘΙΑΣ 38","postcode":"11364","area":"ΚΥΨΕΛΗ"},{"name":"46ο Δημοτικό Σχολείο Αθηνών","street":"ΚΕΑΣ 69-71","postcode":"11255","area":"Α. ΠΑΤΗΣΙΑ"},{"name":"48ο Δημοτικό Σχολείο Αθηνών","street":"ΑΙΛΙΑΝΟΥ 10Α","postcode":"11254","area":"ΑΘΗΝΑ"},{"name":"49ο Δημοτικό Σχολείο Αθηνών","street":"ΑΓΙΩΝ ΑΣΩΜΑΤΩΝ 35-37","postcode":"10553","area":"ΚΕΡΑΜΕΙΚΟΣ"},{"name":"50ο Δημοτικό Σχολείο Αθηνών","street":"ΑΡΙΣΤΟΜΕΝΟΥΣ 101","postcode":"10446","area":"ΠΛ. ΑΤΤΙΚΗΣ"},{"name":"51ο Δημοτικό Σχολείο Αθηνών","street":"ΑΚΟΜΙΝΑΤΟΥ 40","postcode":"10438","area":"ΠΛ. ΒΑΘΗ"},{"name":"52ο Δημοτικό Σχολείο Αθηνών","street":"ΛΙΟΣΙΩΝ 195","postcode":"10445","area":"ΠΛ. ΑΤΤΙΚΗΣ"},{"name":"53ο Δημοτικό Σχολείο Αθηνών","street":"ΤΑΡΣΟΥ 26","postcode":"10434","area":"ΠΛ. ΑΤΤΙΚΗΣ"},{"name":"54ο Δημοτικό Σχολείο Αθηνών","street":"Μ. ΒΟΔΑ 2","postcode":"10439","area":"ΠΛ. ΒΑΘΗ"},{"name":"55ο Δημοτικό Σχολείο Αθηνών","street":"ΛΙΟΣΙΩΝ 42","postcode":"10439","area":"ΠΛ. ΒΑΘΗ"},{"name":"56ο Δημοτικό Σχολείο Αθηνών","street":"ΤΙΜΑΙΟΥ 7","postcode":"10441","area":"ΚΟΛΩΝΟΣ"},{"name":"57ο Δημοτικό Σχολείο Αθηνών","street":"ΔΙΣΤΟΜΟΥ 67","postcode":"10444","area":"ΚΟΛΩΝΟΣ"},{"name":"58ο Δημοτικό Σχολείο Αθηνών","street":"ΛΕΝΟΡΜΑΝ 268","postcode":"10443","area":"ΚΟΛΟΚΥΝΘΟΥ"},{"name":"59ο Δημοτικό Σχολείο Αθηνών","street":"ΔΟΡΔΟΥ 41","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"60ο Δημοτικό Σχολείο Αθηνών","street":"ΑΙΜΟΝΟΣ & ΤΗΛΕΦΑΝΟΥΣ","postcode":"10442","area":"ΚΟΛΩΝΟΣ"},{"name":"61ο Δημοτικό Σχολείο Αθηνών","street":"ΔΙΣΤΟΜΟΥ 67","postcode":"10444","area":"ΚΟΛΩΝΟΣ"},{"name":"62ο Δημοτικό Σχολείο Αθηνών","street":"ΣΜΟΛΙΚΑ & ΚΑΡΑΓΙΑΝΝΗ 2","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"63ο Δημοτικό Σχολείο Αθηνών","street":"Μ. ΚΟΡΑΚΑ 44","postcode":"10445","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"64ο Δημοτικό Σχολείο Αθηνών","street":"Μ. ΑΛΕΞΑΝΔΡΟΥ 63","postcode":"10435","area":"ΜΕΤΑΞΟΥΡΓΕΙΟ"},{"name":"65ο Δημοτικό Σχολείο Αθηνών","street":"ΤΑΫΓΕΤΟΥ 60","postcode":"11255","area":"ΓΚΡΑΒΑ"},{"name":"66ο Δημοτικό Σχολείο Αθηνών","street":"ΑΛΑΜΑΝΑΣ 6","postcode":"10441","area":"ΚΟΛΩΝΟΣ"},{"name":"67ο Δημοτικό Σχολείο Αθηνών","street":"ΣΥΡΡΑΚΟΥ 2","postcode":"10444","area":"ΚΟΛΩΝΟΣ"},{"name":"69ο Δημοτικό Σχολείο Αθηνών","street":"ΤΕΡΤΙΠΗ 42","postcode":"10445","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"70ο Δημοτικό Σχολείο Αθηνών","street":"ΚΑΛΛΙΣΠΕΡΗ 1","postcode":"11742","area":"ΦΙΛΟΠΑΠΠΟΥ"},{"name":"71ο Δημοτικό Σχολείο Αθηνών","street":"ΓΕΝΝΑΙΟΥ ΚΟΛΟΚΟΤΡΩΝΗ 25-27","postcode":"11741","area":"ΚΟΥΚΑΚΙ"},{"name":"72ο Δημοτικό Σχολείο Αθηνών","street":"ΑΚΤΑΙΟΥ 2-4","postcode":"11851","area":"ΘΗΣΕΙΟ"},{"name":"73ο Δημοτικό Σχολείο Αθηνών","street":"ΤΡΩΩΝ 2","postcode":"11851","area":"Α. ΠΕΤΡΑΛΩΝΑ"},{"name":"74ο Δημοτικό Σχολείο Αθηνών","street":"ΑΔΡΙΑΝΟΥ 106","postcode":"10556","area":"ΠΛΑΚΑ"},{"name":"75ο Δημοτικό Σχολείο Αθηνών","street":"ΡΙΚΑΚΗ 9","postcode":"10445","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"76ο Δημοτικό Σχολείο Αθηνών","street":"ΚΥΚΛΩΠΩΝ 6","postcode":"11852","area":"Α. ΠΕΤΡΑΛΩΝΑ"},{"name":"77ο Δημοτικό Σχολείο Αθηνών","street":"ΤΡΩΩΝ 18","postcode":"11851","area":"Α. ΠΕΤΡΑΛΩΝΑ"},{"name":"79ο Δημοτικό Σχολείο Αθηνών","street":"ΕΥΓΕΝΙΟΥ ΚΑΡΑΒΙΑ 9","postcode":"11254","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"81ο Δημοτικό Σχολείο Αθηνών","street":"ΣΚΑΜΒΩΝΙΔΩΝ 46","postcode":"11853","area":"Κ. ΠΕΤΡΑΛΩΝΑ"},{"name":"85ο Δημοτικό Σχολείο Αθηνών","street":"ΣΠ. ΠΑΤΣΗ 56","postcode":"11855","area":"ΒΟΤΑΝΙΚΟΣ"},{"name":"86ο Δημοτικό Σχολείο Αθηνών","street":"ΑΙΓΙΝΗΣ 61","postcode":"11362","area":"ΚΥΨΕΛΗ"},{"name":"87ο Δημοτικό Σχολείο Αθηνών","street":"ΟΡΦΕΩΣ 58","postcode":"11854","area":"ΒΟΤΑΝΙΚΟΣ"},{"name":"88ο Δημοτικό Σχολείο Αθηνών","street":"ΧΑΛΚΟΜΑΤΑΔΩΝ 42","postcode":"11142","area":"ΡΙΖΟΥΠΟΛΗ"},{"name":"89ο Δημοτικό Σχολείο Αθηνών","street":"ΚΡΟΤΩΝΟΣ 4","postcode":"11631","area":"ΑΓ. ΑΡΤΕΜΙΟΣ"},{"name":"90ο Δημοτικό Σχολείο Αθηνών","street":"ΑΜΦΙΚΡΑΤΟΥΣ 6","postcode":"11631","area":"ΑΓ. ΑΡΤΕΜΙΟΣ"},{"name":"91ο Δημοτικό Σχολείο Αθηνών","street":"ΦΙΛΟΛΑΟΥ 163","postcode":"11632","area":"ΑΓ. ΑΡΤΕΜΙΟΣ"},{"name":"92ο Δημοτικό Σχολείο Αθηνών","street":"ΕΚΑΤΑΙΟΥ 80","postcode":"11743","area":"Ν. ΚΟΣΜΟΣ"},{"name":"93ο Δημοτικό Σχολείο Αθηνών","street":"ΠΥΘΕΟΥ 9","postcode":"11743","area":"Ν. ΚΟΣΜΟΣ"},{"name":"94ο Δημοτικό Σχολείο Αθηνών","street":"ΛΑΓΟΥΜΙΤΖΗ 55","postcode":"11745","area":"Ν. ΚΟΣΜΟΣ"},{"name":"96ο Δημοτικό Σχολείο Αθηνών","street":"ΦΩΤΟΜΑΡΑ 60","postcode":"11745","area":"Ν. ΚΟΣΜΟΣ"},{"name":"99ο Δημοτικό Σχολείο Αθηνών","street":"ΥΓΕΙΑΣ 11Α","postcode":"10446","area":"ΑΓ. ΠΑΝΤΕΛΕΗΜΟΝΑΣ"},{"name":"100ο Δημοτικό Σχολείο Αθηνών","street":"ΠΥΡΡΑΣ 15","postcode":"11745","area":"Ν. ΚΟΣΜΟΣ"},{"name":"101ο Δημοτικό Σχολείο Αθηνών","street":"ΠΟΛΥΔΟΥΡΗ 4","postcode":"11141","area":"ΚΥΠΡΙΑΔΟΥ"},{"name":"102ο Δημοτικό Σχολείο Αθηνών","street":"ΒΑΦΕΙΟΧΩΡΙΟΥ 25","postcode":"11476","area":"ΠΟΛΥΓΩΝΟ"},{"name":"103ο Δημοτικό Σχολείο Αθηνών","street":"ΣΤΙΟΥΑΡΤ 21","postcode":"11745","area":"Ν. ΚΟΣΜΟΣ"},{"name":"104ο Δημοτικό Σχολείο Αθηνών","street":"ΜΑΙΑΝΔΡΟΥΠΟΛΕΩΣ 42","postcode":"11524","area":"ΑΜΠΕΛΟΚΗΠΟΙ"},{"name":"105ο Δημοτικό Σχολείο Αθηνών","street":"ΣΟΥΚΑ & ΧΟΡΜΟΠΟΥΛΟΥ","postcode":"11522","area":"ΠΟΛΥΓΩΝΟ"},{"name":"106ο Δημοτικό Σχολείο Αθηνών","street":"ΠΟΝΤΟΥ & ΑΓ. ΘΩΜΑ","postcode":"16346","area":"ΓΟΥΔΗ"},{"name":"107ο Δημοτικό Σχολείο Αθηνών","street":"ΘΕΟΛΟΓΟΥ ΙΩΑΝΝΙΔΗ 7-11","postcode":"11524","area":"Ν. ΦΙΛΟΘΕΗ"},{"name":"108ο Δημοτικό Σχολείο Αθηνών","street":"ΘΗΡΑΣ 110","postcode":"10446","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"109ο Δημοτικό Σχολείο Αθηνών","street":"ΘΕΟΤΟΚΟΠΟΥΛΟΥ 50","postcode":"11144","area":"Α. ΠΑΤΗΣΙΑ"},{"name":"111ο Δημοτικό Σχολείο Αθηνών","street":"ΚΕΔΡΗΝΟΥ & ΤΣΕΛΙΟΥ","postcode":"11522","area":"ΑΡΕΙΟ ΠΑΓΟΣ"},{"name":"112ο Δημοτικό Σχολείο Αθηνών","street":"ΤΑΫΓΕΤΟΥ 60","postcode":"11255","area":"ΓΚΡΑΒΑ"},{"name":"113ο Δημοτικό Σχολείο Αθηνών","street":"ΣΙΤΑΚΗΣ 64","postcode":"11142","area":"ΛΑΜΠΡΙΝΗ"},{"name":"117ο Δημοτικό Σχολείο Αθηνών","street":"ΜΑΧΗΣ ΑΝΑΛΑΤΟΥ 70","postcode":"11745","area":"Ν. ΚΟΣΜΟΣ"},{"name":"120ο Δημοτικό Σχολείο Αθηνών","street":"ΚΟΚΚΕΡΕΛ 14","postcode":"11146","area":"Α. ΚΥΨΕΛΗ"},{"name":"123ο Δημοτικό Σχολείο Αθηνών","street":"ΑΜΦΙΚΡΑΤΟΥΣ 6","postcode":"11631","area":"ΑΓ. ΑΡΤΕΜΙΟΣ"},{"name":"127ο Δημοτικό Σχολείο Αθηνών","street":"ΚΑΛΛΙΠΟΛΕΩΣ 10","postcode":"10444","area":"ΚΟΛΩΝΟΣ"},{"name":"128ο Δημοτικό Σχολείο Αθηνών","street":"ΚΑΛΑΜΑ 2","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"129ο Δημοτικό Σχολείο Αθηνών","street":"ΠΡΟΜΠΟΝΑ 44","postcode":"11143","area":"Α. ΠΑΤΗΣΙΑ"},{"name":"130ο Δημοτικό Σχολείο Αθηνών","street":"ΠΡΕΤΕΝΤΕΡΗ 20","postcode":"11145","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"132ο Δημοτικό Σχολείο Αθηνών","street":"ΤΑΫΓΕΤΟΥ 60","postcode":"11255","area":"ΓΡΑΒΑ"},{"name":"133ο Δημοτικό Σχολείο Αθηνών","street":"ΤΡΟΙΑΣ 6","postcode":"11362","area":"ΚΥΨΕΛΗ"},{"name":"134ο Δημοτικό Σχολείο Αθηνών","street":"ΑΓ. ΦΩΤΕΙΝΗΣ 4","postcode":"11363","area":"Ν. ΚΥΨΕΛΗ"},{"name":"135ο Δημοτικό Σχολείο Αθηνών","street":"ΜΟΜΦΕΡΑΤΟΥ 94","postcode":"11474","area":"ΓΚΥΖΗ"},{"name":"137ο Δημοτικό Σχολείο Αθηνών","street":"ΑΛΚΙΦΡΟΝΟΣ 51-55","postcode":"11853","area":"Κ. ΠΕΤΡΑΛΩΝΑ"},{"name":"139ο Δημοτικό Σχολείο Αθηνών","street":"ΜΑΒΙΛΗ 11","postcode":"11141","area":"Α. ΠΑΤΗΣΙΑ"},{"name":"141ο Δημοτικό Σχολείο Αθηνών","street":"ΑΧΑΡΝΩΝ 399","postcode":"11143","area":"ΑΓ. ΕΛΕΥΘΕΡΙΟΣ"},{"name":"142ο Δημοτικό Σχολείο Αθηνών","street":"ΚΡΥΣΤΑΛΛΗ 10-16","postcode":"11141","area":"ΚΥΠΡΙΑΔΟΥ"},{"name":"144ο Δημοτικό Σχολείο Αθηνών","street":"ΧΑΤΖΗΑΠΟΣΤΟΛΟΥ & ΜΕΤΟΧΙΤΗ","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"145ο Δημοτικό Σχολείο Αθηνών","street":"ΝΙΚ. ΓΡΗΓΟΡΑ 5-7","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"149ο Δημοτικό Σχολείο Αθηνών","street":"ΑΓΑΘΟΔΑΙΜΟΝΟΣ 41","postcode":"11853","area":"Κ. ΠΕΤΡΑΛΩΝΑ"},{"name":"150ο Δημοτικό Σχολείο Αθηνών","street":"ΚΟΔΡΙΓΚΤΩΝΟΣ 26","postcode":"11251","area":"ΠΛ. ΒΙΚΤΩΡΙΑΣ"},{"name":"152ο Δημοτικό Σχολείο Αθηνών","street":"ΜΗΛΙΑΡΑΚΗ 57-59","postcode":"11145","area":"Κ. ΠΑΤΗΣΙΑ"},{"name":"162ο Δημοτικό Σχολείο Αθηνών","street":"ΖΗΝΟΔΩΡΟΥ 23","postcode":"10442","area":"ΚΟΛΟΚΥΝΘΟΥ"},{"name":"165ο Δημοτικό Σχολείο Αθηνών","street":"ΚΥΠΡΟΥ 43","postcode":"11253","area":"ΠΛ. ΑΜΕΡΙΚΗΣ"},{"name":"170ο Δημοτικό Σχολείο Αθηνών","street":"ΘΗΡΑΣ 110","postcode":"10446","area":"ΠΛ. ΑΜΕΡΙΚΗΣ"},{"name":"172ο Δημοτικό Σχολείο Αθηνών","street":"ΣΚOΠΕΛΟΥ 67-71","postcode":"11363","area":"Ν. ΚΥΨΕΛΗ"},{"name":"173ο Δημοτικό Σχολείο Αθηνών","street":"ΑΡΙΟΒΑΡΖΑΝΟΥ & ΠΡΟΜΠΟΝΑ","postcode":"11143","area":"ΠΡΟΜΠΟΝΑ"},{"name":"174ο Δημοτικό Σχολείο Αθηνών","street":"ΠΑΝΔΟΣΙΑΣ 2","postcode":"11142","area":"ΛΑΜΠΡΙΝΗ"},{"name":"1ο Δημοτικό Σχολείο Βύρωνα","street":"ΚΩΝΣΤΑΝΙΛΙΕΡΗ","postcode":"16231","area":"ΒΥΡΩΝΑΣ"},{"name":"3ο Δημοτικό Σχολείο Βύρωνα","street":"ΜΕΣΟΛΟΓΓΙΟΥ & ΕΡΥΘΡΑΙΑΣ","postcode":"16231","area":"ΒΥΡΩΝΑΣ"},{"name":"4ο Δημοτικό Σχολείο Βύρωνα","street":"ΕΛΛΗΝΩΝ ΑΞΙΩΜΑΤΙΚΩΝ 8","postcode":"16232","area":"ΒΥΡΩΝΑΣ"},{"name":"5ο Δημοτικό Σχολείο Βύρωνα","street":"ΤΑΤΑΟΥΛΩΝ 1 & ΒΥΖΑΝΤΙΟΥ","postcode":"16232","area":"ΒΥΡΩΝΑΣ"},{"name":"6ο Δημοτικό Σχολείο Βύρωνα","street":"ΑΔΑΝΩΝ 3","postcode":"16231","area":"ΒΥΡΩΝΑΣ"},{"name":"7ο Δημοτικό Σχολείο Βύρωνα","street":"ΣΩΚΙΩΝ 38","postcode":"16231","area":"N. ΕΛΒΕΤΙΑ"},{"name":"8ο Δημοτικό Σχολείο Βύρωνα","street":"ΑΙΓΙΑΛΕΙΑΣ 33Α","postcode":"16233","area":"ΒΥΡΩΝΑΣ"},{"name":"9ο Δημοτικό Σχολείο Βύρωνα","street":"ΘΥΜΑΤΩΝ ΠΟΛΕΜΟΥ 27","postcode":"16233","area":"ΚΑΡΕΑΣ"},{"name":"10ο Δημοτικό Σχολείο Βύρωνα","street":"ΙΩΑΝΝΙΝΩΝ 12","postcode":"16232","area":"ΜΕΤΑΜΟΡΦΩΣΗ"},{"name":"11ο Δημοτικό Σχολείο Βύρωνα","street":"ΒΥΖΑΝΤΙΟΥ & ΤΑΤΑΟΥΛΩΝ 1","postcode":"16233","area":"ΒΥΡΩΝΑΣ"},{"name":"12ο Δημοτικό Σχολείο Βύρωνα","street":"ΙΑΚ. ΜΕΡΚΟΥΡΙΑΔΗ 20","postcode":"16232","area":"ΒΥΡΩΝΑΣ"},{"name":"1ο Δημοτικό Σχολείο Γαλατσίου","street":"Λ. ΓΑΛΑΤΣΙΟΥ 86","postcode":"11146","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"2ο Δημοτικό Σχολείο Γαλατσίου","street":"ΔΡΥΟΠΙΔΟΣ 9","postcode":"11147","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"3ο Δημοτικό Σχολείο Γαλατσίου","street":"ΠΡΩΤΟΠΑΠΑΔΑΚΗ 8","postcode":"11147","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"4ο Δημοτικό Σχολείο Γαλατσίου","street":"ΠΡΩΤΟΠΑΠΑΔΑΚΗ 8","postcode":"11147","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"5ο Δημοτικό Σχολείο Γαλατσίου","street":"ΟΡΦΑΝΙΔΟΥ 101","postcode":"11146","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"7ο Δημοτικό Σχολείο Γαλατσίου","street":"ΔΡΥΑΔΩΝ 43","postcode":"11146","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"9ο Δημοτικό Σχολείο Γαλατσίου","street":"ΗΡΟΔΟΤΟΥ 3","postcode":"11147","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"11ο Δημοτικό Σχολείο Γαλατσίου","street":"ΚΥΜΟΘΟΗΣ 16","postcode":"11146","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"12ο Δημοτικό Σχολείο Γαλατσίου","street":"Λ. ΓΑΛΑΤΣΙΟΥ 66","postcode":"11146","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"16ο Δημοτικό Σχολείο Γαλατσίου","street":"ΦΙΓΑΛΕΙΑΣ 67","postcode":"11147","area":"ΓΑΛΑΤΣΙΟΥ"},{"name":"1ο Δημοτικό Σχολείο Δάφνης","street":"ΕΛΛΗΣ 19","postcode":"17235","area":"ΔΑΦΝΗ"},{"name":"2ο Δημοτικό Σχολείο Δάφνης","street":"ΑΛΕΞΑΝΔΡΕΙΑΣ 60","postcode":"17235","area":"ΔΑΦΝΗ"},{"name":"4ο Δημοτικό Σχολείο Δάφνης","street":"ΠΑΠΑΝΑΣΤΑΣΙΟΥ 72","postcode":"17235","area":"ΔΑΦΝΗ"},{"name":"5ο Δημοτικό Σχολείο Δάφνης","street":"ΓΡΑΜΜΟΥ 1","postcode":"17234","area":"ΔΑΦΝΗ"},{"name":"6ο Δημοτικό Σχολείο Δάφνης","street":"ΓΥΜΝΑΣΤΗΡΙΟΥ 64","postcode":"12737","area":"ΔΑΦΝΗ"},{"name":"7ο Δημοτικό Σχολείο Δάφνης","street":"ΕΘΝ. ΑΝΤΙΣΤΑΣΗΣ & ΑΡΙΣΤΟΤΕΛΟΥΣ 9","postcode":"17236","area":"ΔΑΦΝΗ"},{"name":"8ο Δημοτικό Σχολείο Δάφνης","street":"ΕΛΕΥΘΕΡΙΑΣ 2Α","postcode":"17234","area":"ΔΑΦΝΗ"},{"name":"9ο Δημοτικό Σχολείο Δάφνης","street":"ΖΩΟΔΟΧΟΥ ΠΗΓΗΣ & ΚΑΒΑΛΑΣ","postcode":"17234","area":"ΔΑΦΝΗ"},{"name":"1ο Δημοτικό Σχολείο Ζωγράφου","street":"ΗΡ. ΠΟΛΥΤΕΧΝΕΙΟΥ 1","postcode":"15773","area":"ΖΩΓΡΑΦΟΥ"},{"name":"2ο Δημοτικό Σχολείο Ζωγράφου","street":"ΕΥΝΟΜΙΑΣ 2","postcode":"15772","area":"ΖΩΓΡΑΦΟΥ"},{"name":"3ο Δημοτικό Σχολείο Ζωγράφου","street":"ΚΡΙΝΩΝ 28","postcode":"15772","area":"ΖΩΓΡΑΦΟΥ"},{"name":"4ο Δημοτικό Σχολείο Ζωγράφου","street":"Μ.ΑΛΕΞΑΝΔΡΟΥ","postcode":"15773","area":"ΖΩΓΡΑΦΟΥ"},{"name":"5ο Δημοτικό Σχολείο Ζωγράφου","street":"ΠΕΡΙΑΝΔΡΟΥ 27","postcode":"15771","area":"ΖΩΓΡΑΦΟΥ"},{"name":"6ο Δημοτικό Σχολείο Ζωγράφου","street":"ΠΕΡΙΑΝΔΡΟΥ 27","postcode":"15771","area":"ΖΩΓΡΑΦΟΥ"},{"name":"8ο Δημοτικό Σχολείο Ζωγράφου","street":"ΜΑΚΡΥΓΙΑΝΝΗ 44Α","postcode":"15772","area":"ΖΩΓΡΑΦΟΥ"},{"name":"12ο Δημοτικό Σχολείο Ζωγράφου","street":"ΜΑΚΡΥΓΙΑΝΝΗ 44Α","postcode":"15772","area":"ΖΩΓΡΑΦΟΥ"},{"name":"19ο Δημοτικό Σχολείο Ζωγράφου","street":"ΗΡ. ΠΟΛΥΤΕΧΝΕΙΟΥ 1","postcode":"15773","area":"ΖΩΓΡΑΦΟΥ"},{"name":"1ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΦΛΕΜΙΝΓΚ 1","postcode":"16345","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"2ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΠΟΥΣΟΥΛΙΔΟΥ 10","postcode":"16346","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"3ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΚΙΘΑΙΡΩΝΟΣ & ΣΟΦΟΥΛΗ 1","postcode":"16344","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"4ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΣΟΦ. ΒΕΝΙΖΕΛΟΥ 83","postcode":"16346","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"5ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΑΓΑΜΕΜΝΟΝΟΣ 1","postcode":"16343","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"6ο Δημοτικό Σχολείο Ηλιούπολης","street":"Μ. ΑΝΤΥΠΑ 34","postcode":"16346","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"7ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΓΡΑΜΜΟΥ 30 & ΜΑΤΣΟΥΚΑ","postcode":"16345","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"8ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΜΕΣΣΗΝΙΑΣ & ΚΕΦΑΛΛΗΝΙΑΣ","postcode":"16342","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"9ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΙΟΝΙΩΝ ΝΗΣΩΝ 35","postcode":"17237","area":"ΥΜΗΤΤΟΣ"},{"name":"10ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΜΥΚΟΝΟΥ 34","postcode":"16346","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"11ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΚΟΤΖΙΑ & ΣΤΟΥΡΝΑΡΑ 1","postcode":"16346","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"12ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΦΑΝΑΡΙΩΤΩΝ 8-10","postcode":"16343","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"13ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΗΡΩΣ ΚΩΝ/ΠΟΥΛΟΥ & Θ. ΛΟΥΚΙΔΟΥ 3","postcode":"16341","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"15ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΘΡΑΚΗΣ & ΑΛΙΜΟΥΝΤΟΣ","postcode":"16341","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"17ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΜΕΣΣΗΝΙΑΣ & ΚΕΦΑΛΛΗΝΙΑΣ","postcode":"16342","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"20ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΑΓΑΜΕΜΝΟΝΟΣ 1","postcode":"16343","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"21ο Δημοτικό Σχολείο Ηλιούπολης","street":"ΤΕΜΠΟΝΕΡΑ & ΜΑΤΣΟΥΚΑ","postcode":"16345","area":"ΗΛΙΟΥΠΟΛΗ"},{"name":"1ο Δημοτικό Σχολείο Καισαριανής","street":"ΕΘΝΙΚΗΣ ΑΝΤΙΣΤΑΣΕΩΣ 113","postcode":"16121","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"2ο Δημοτικό Σχολείο Καισαριανής","street":"ΕΙΡΗΝΗΣ 19","postcode":"16122","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"3ο Δημοτικό Σχολείο Καισαριανής","street":"ΗΡΩΣ ΚΩΝΣΤΑΝΤΟΠΟΥΛΟΥ 13Α","postcode":"16121","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"4ο Δημοτικό Σχολείο Καισαριανής","street":"ΧΙΟΥ & ΜΑΝΩΛΙΔΗ","postcode":"16233","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"6ο Δημοτικό Σχολείο Καισαριανής","street":"ΗΡΩΣ ΚΩΝΣΤΑΝΤΟΠΟΥΛΟΥ 13Α","postcode":"16121","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"7ο Δημοτικό Σχολείο Καισαριανής","street":"ΕΘΝΙΚΗΣ ΑΝΤΙΣΤΑΣΕΩΣ 113","postcode":"16122","area":"ΚΑΙΣΑΡΙΑΝΗ"},{"name":"1ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΛΑΧΑΝΑ 1-3","postcode":"14341","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"2ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΕΦΕΣΟΥ 1","postcode":"14341","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"3ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΓΡΑΜΜΟΥ 2","postcode":"14342","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"4ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΛΑΧΑΝΑ 1-3","postcode":"14342","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"5ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΝΙΚΗΤΑΡΑ 28","postcode":"14342","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"6ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΠΕΛΑΣΓΩΝ 16","postcode":"14342","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"7ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΠΑΡΟΔΟΣ ΠΑΠΑΝΙΚΟΛΗ","postcode":"14342","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"8ο Δημοτικό Σχολείο Νέας Φιλαδέλφειας","street":"ΜΑΙΑΝΔΡΟΥ 85","postcode":"14341","area":"Ν. ΦΙΛΑΔΕΛΦΕΙΑ"},{"name":"1ο Δημοτικό Σχολείο Νέας Χαλκηδόνας","street":"ΓΡΗΓΟΡΙΟΥ Ε' 1","postcode":"14343","area":"Ν. ΧΑΛΚΗΔΟΝΑ"},{"name":"2ο Δημοτικό Σχολείο Νέας Χαλκηδόνας","street":"ΑΓ. ΑΝΑΡΓΥΡΩΝ 2","postcode":"14343","area":"Ν. ΧΑΛΚΗΔΟΝΑ"},{"name":"1ο Δημοτικό Σχολείο Υμηττού","street":"ΠΑΠΑΣΤΡΑΤΟΥ 34","postcode":"17237","area":"ΥΜΗΤΤΟΣ"},{"name":"2ο Δημοτικό Σχολείο Υμηττού","street":"ΔΟΡΥΛΑΙΟΥ 2-4","postcode":"17237","area":"ΥΜΗΤΤΟΣ"},{"name":"3ο Δημοτικό Σχολείο Υμηττού","street":"ΚΑΡΑΟΛΗ & ΙΟΝ.ΝΗΣΩΝ 35","postcode":"17237","area":"ΥΜΗΤΤΟΣ"},{"name":"4ο Δημοτικό Σχολείο Υμηττού","street":"ΠΡΟΥΣΗΣ 1","postcode":"17236","area":"ΥΜΗΤΤΟΣ"},{"name":"Νοσοκομείου Παίδων \"Αγία Σοφία\"","street":"Θηβών & Μεσογείων Ασίας","postcode":"11527","area":"ΓΟΥΔΗ"},{"name":"Νοσοκομείου Παίδων \"Αγλαΐα Κυριακού\"","street":"Θηβών & Λεβαδείας 1","postcode":"11527","area":"ΓΟΥΔΗ"},{"name":"Πρότυπο Πειραματικό Δημοτικό Σχολείο Πανεπιστημίου Αθηνών (Μονοθέσιο, Μαράσλειο)","street":"Μαρασλή 4","postcode":"10676","area":"ΚΟΛΩΝΑΚΙ"},{"name":"1ο 12/Θ Πειραματικό Πανεπιστημίου Αθηνών (Μαράσλειο)","street":"Μαρασλή 4","postcode":"10676","area":"ΚΟΛΩΝΑΚΙ"},{"name":"3/Θέσιο Πειραματικό Δημοτικό Σχολείο Πανεπιστημίου Αθηνών (Μαράσλειο)","street":"Μαρασλή 4","postcode":"10676","area":"ΚΟΛΩΝΑΚΙ"},{"name":"6/Θ Πειραματικό Πανεπιστημίου Αθηνών (Π.Σ.Π.Α.)","street":"Σκουφά 43","postcode":"10673","area":"ΚΟΛΩΝΑΚΙ"},{"name":"1ο Ειδικό Δημοτικό Σχολείο ΕΛΕΠΑΠ","street":"Κόνωνος 16","postcode":"11634","area":"ΠΑΓΚΡΑΤΙ"},{"name":"2ο Ειδικό Δημοτικό Σχολείο ΕΛΕΠΑΠ","street":"Αριστάρχου 24","postcode":"11634","area":"ΠΑΓΚΡΑΤΙ"},{"name":"4ο Ειδικό Δημοτικό Σχολείο Αθηνών","street":"Ταϋγέτου 60","postcode":"11253","area":"ΓΚΡΑΒΑ"},{"name":"6ο Ειδικό Δημοτικό Σχολείο Αθηνών","street":"Τριανταφυλλοπούλου & Χατζηαποστόλου","postcode":"10443","area":"ΣΕΠΟΛΙΑ"},{"name":"9ο Ειδικό Δημοτικό Σχολείο Αθηνών","street":"Πόντου & Αγίου Θωμά","postcode":"11527","area":"ΓΟΥΔΙ"},{"name":"10ο Ειδικό Δημοτικό Σχολείο Αθηνών","street":"Μαρασλή 4","postcode":"10676","area":"ΚΟΛΩΝΑΚΙ"},{"name":"Ειδικό Μ.Δ.Δ.Ε. Καισαριανής","street":"Σολομωνίδου 68","postcode":"16121","area":"ΚΑΙΣΑΡΙΑΝΗ"}]"""
SCHOOLS_DB = json.loads(SCHOOLS_JSON)

# Γενικές λέξεις που αγνοούνται όταν συγκρίνουμε ονόματα σχολείων
GENERIC_WORDS = {
    "σχολειο", "σχολειου", "σχολειων", "δημοτικο", "δημοτικου", "δημ",
    "δ.σ", "δσ", "νηπιαγωγειο", "νηπιαγωγειου", "νηπ", "ν/γ", "νγ",
    "ολοημερο", "ολοημερου", "ειδικο", "ειδικης", "αγωγης", "πρωτυπο",
    "πειραματικο", "τμημα", "ενταξης", "της", "του", "και",
}


def strip_accents(text):
    """Αφαιρεί τόνους (π.χ. 'ά'->'α') κρατώντας το ελληνικό αλφάβητο."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def norm(text):
    """Πεζά + χωρίς τόνους + χωρίς διπλά κενά, για ασφαλείς συγκρίσεις κειμένου."""
    return re.sub(r"\s+", " ", strip_accents(text).strip()).lower()


def extract_number_and_rest(name):
    """Από '32ο Δημοτικό Σχολείο Αθηνών' -> ('32', 'Δημοτικό Σχολείο Αθηνών')."""
    m = re.match(r"\s*(\d+)\s*[οΟoO][ςΣ']?\s*(.*)$", name)
    if m:
        return m.group(1), m.group(2).strip()
    return None, name


# Προ-υπολογισμός: αριθμός σχολείου + normalized name για κάθε εγγραφή της βάσης
for _entry in SCHOOLS_DB:
    _num, _ = extract_number_and_rest(_entry["name"])
    _entry["_number"] = _num
    _entry["_norm_name"] = norm(_entry["name"])


def find_in_database(name):
    """Ψάχνει το σχολείο μέσα στην ενσωματωμένη επίσημη βάση (Α' Αθήνας).
    Επιστρέφει (entry, score) ή (None, 0)."""
    number, _ = extract_number_and_rest(name)
    target = norm(name)

    candidates = SCHOOLS_DB
    if number:
        same_number = [e for e in SCHOOLS_DB if e["_number"] == number]
        if same_number:
            candidates = same_number

    best, best_score = None, 0.0
    for entry in candidates:
        score = difflib.SequenceMatcher(None, target, entry["_norm_name"]).ratio()
        if score > best_score:
            best_score, best = score, entry
    return best, best_score


def geocode_photon(address, tries=2):
    """Εναλλακτικός geocoder (Komoot Photon, βασισμένος σε OSM δεδομένα, χωρίς κλειδί).
    Δεν ανήκει στο OpenStreetMap Foundation, οπότε δεν επηρεάζεται από τα μπλοκ IP
    που εφαρμόζει το nominatim.openstreetmap.org σε πολλά cloud hosting (π.χ. Streamlit Cloud)."""
    errors = []
    for _ in range(tries):
        try:
            r = requests.get(
                "https://photon.komoot.io/api/",
                params={"q": address, "limit": 1, "lang": "en"},
                headers={"User-Agent": "teacher-closest-school-finder-webapp"},
                timeout=10,
            )
            r.raise_for_status()
            feats = r.json().get("features", [])
            if feats:
                lon, lat = feats[0]["geometry"]["coordinates"]
                return (lat, lon), errors
            errors.append("Photon: καμία αντιστοίχιση")
            break
        except Exception as e:
            errors.append(f"Photon: {e}")
            time.sleep(1)
    return None, errors


def geocode_nominatim(addr, tries=3):
    errors = []
    for _ in range(tries):
        try:
            loc = geolocator.geocode(addr, timeout=10)
            if loc:
                return (loc.latitude, loc.longitude), errors
            errors.append("Nominatim: καμία αντιστοίχιση")
            break
        except Exception as e:
            errors.append(f"Nominatim: {e}")
            time.sleep(1)
    return None, errors


def geocode_address(address, tries=3):
    """Δοκιμάζει πρώτα Photon και μετά Nominatim. Επιστρέφει (coords, debug_errors)."""
    addr = address.strip()
    if not re.search(r"ελλ[αά]δα|greece", addr, re.IGNORECASE):
        addr = addr + ", Ελλάδα"

    coords, err1 = geocode_photon(addr, tries=2)
    if coords:
        return coords, []

    coords, err2 = geocode_nominatim(addr, tries=tries)
    if coords:
        return coords, []

    return None, err1 + err2


def clean_school_name(raw_line):
    line = raw_line.strip()
    line = re.sub(r"\(.*?\)", "", line)
    line = re.sub(r"^\d+[\.\)]\s*", "", line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


def looks_like_school_line(line):
    keywords = ["ΔΗΜΟΤΙΚ", "ΝΗΠΙΑΓΩΓ", "ΣΧΟΛΕΙ", "Δ.Σ", "Ν/Γ", "ΟΛΟΗΜΕΡ", "ΕΙΔΙΚΟ", "ΕΛΕΠΑΠ"]
    upper = line.upper()
    return any(k in upper for k in keywords)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def query_overpass(name):
    """Εφεδρική αναζήτηση στο OpenStreetMap, μόνο για σχολεία που ΔΕΝ βρέθηκαν
    στην ενσωματωμένη επίσημη βάση (π.χ. σχολεία άλλης Διεύθυνσης)."""
    s, w, n, e = ATTICA_BBOX
    number, _rest = extract_number_and_rest(name)
    if number:
        name_regex = rf"^\s*{number}\s*[οΟoO]"
    else:
        name_regex = re.escape(name)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"school|kindergarten"]["name"~"{name_regex}",i]({s},{w},{n},{e});
      way["amenity"~"school|kindergarten"]["name"~"{name_regex}",i]({s},{w},{n},{e});
      relation["amenity"~"school|kindergarten"]["name"~"{name_regex}",i]({s},{w},{n},{e});
    );
    out center tags;
    """
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception:
        return []


def best_osm_match(name, elements):
    target = norm(name)
    best, best_score = None, 0.0
    for el in elements:
        cand_name = el.get("tags", {}).get("name", "")
        score = difflib.SequenceMatcher(None, target, norm(cand_name)).ratio()
        if score > best_score:
            best_score, best = score, el
    return best, best_score


def get_osm_coords(el):
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    center = el.get("center")
    if center:
        return center["lat"], center["lon"]
    return None


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def locate_school(name):
    """Επιστρέφει (lat, lon, address, method, matched_name) ή None.
    Σειρά προτεραιότητας:
    1) Ενσωματωμένη επίσημη βάση Α' Αθήνας (πιο αξιόπιστο - πραγματική διεύθυνση)
    2) OpenStreetMap (αναζήτηση με βάση το όνομα, εφεδρικά)
    3) Photon / Nominatim (αναζήτηση με βάση το όνομα ως τοποθεσία, έσχατη λύση)
    """
    # 1) Επίσημη βάση
    entry, score = find_in_database(name)
    if entry and score > 0.30:
        full_address = f"{entry['street']}, {entry['postcode']} {entry['area']}, Αθήνα, Ελλάδα"
        coords, _ = geocode_address(full_address)
        if coords:
            display_address = f"{entry['street']}, {entry['postcode']} {entry['area']}"
            return coords[0], coords[1], display_address, "Επίσημη λίστα Α' Αθήνας 2024-25", entry["name"]

    # 2) OpenStreetMap POI αναζήτηση (π.χ. σχολεία εκτός Α' Αθήνας)
    elements = query_overpass(name)
    if elements:
        el, osm_score = best_osm_match(name, elements)
        if el and osm_score > 0.30:
            coords = get_osm_coords(el)
            if coords:
                tags = el.get("tags", {})
                addr_parts = [tags.get("addr:street", ""), tags.get("addr:housenumber", ""), tags.get("addr:city", "")]
                address = " ".join(p for p in addr_parts if p).strip()
                if not address:
                    address = "Διεύθυνση μη διαθέσιμη στο OpenStreetMap"
                matched_name = tags.get("name", name)
                return coords[0], coords[1], address, "OpenStreetMap (κατά προσέγγιση)", matched_name

    # 3) Έσχατη λύση: αναζήτηση ονόματος ως τοποθεσία
    for attempt_query in (f"{name}, Αθήνα, Ελλάδα", f"{name}, Αττική, Ελλάδα"):
        coords, _ = geocode_photon(attempt_query, tries=1)
        if coords:
            return coords[0], coords[1], "Άγνωστη ακριβής διεύθυνση (κατά προσέγγιση)", "Photon (κατά προσέγγιση)", name
        try:
            loc = geolocator.geocode(attempt_query, timeout=10)
            if loc:
                return loc.latitude, loc.longitude, loc.address, "Nominatim (κατά προσέγγιση)", name
        except Exception:
            time.sleep(1)
    return None


# =======================================================================
# UI
# =======================================================================
st.set_page_config(page_title="Πλησιέστερο Σχολείο", page_icon="🏫", layout="wide")
st.title("🏫 Εύρεση πλησιέστερου σχολείου")
st.caption(f"Πρωτοβάθμια Εκπαίδευση (Δημοτικά) - Αθήνα · {len(SCHOOLS_DB)} σχολεία στην ενσωματωμένη βάση (Α' Αθήνας 2024-25)")

col1, col2 = st.columns([1, 1])

with col1:
    home_address = st.text_input(
        "Διεύθυνση κατοικίας σου",
        placeholder="π.χ. Πατησίων 100, Αθήνα",
    )

with col2:
    schools_raw = st.text_area(
        "Λίστα σχολείων (ένα σχολείο ανά γραμμή)",
        height=150,
        placeholder="32ο σχολείο Αθηνών\n2ο σχολείο Καισαριανής\n5ο σχολείο Νέας Φιλαδέλφειας",
    )

run = st.button("🔎 Βρες αποστάσεις & χάρτη", type="primary")

if run:
    if not home_address.strip():
        st.error("Συμπλήρωσε πρώτα τη διεύθυνση κατοικίας σου.")
        st.stop()
    if not schools_raw.strip():
        st.error("Επικόλλησε τη λίστα σχολείων.")
        st.stop()

    with st.spinner("Εντοπισμός διεύθυνσης κατοικίας..."):
        home_coords, geocode_errors = geocode_address(home_address)

    if not home_coords:
        st.error(
            "Δεν μπόρεσα να εντοπίσω αυτή τη διεύθυνση. Δοκίμασε πιο συγκεκριμένη μορφή "
            "(οδός, αριθμός, περιοχή)."
        )
        if geocode_errors:
            with st.expander("Τεχνικές λεπτομέρειες (για αν χρειαστεί υποστήριξη)"):
                for e in geocode_errors:
                    st.code(e)
        st.stop()

    st.success(f"Το σπίτι εντοπίστηκε στις συντεταγμένες: {home_coords}")

    raw_lines = [l for l in schools_raw.splitlines() if l.strip()]
    school_names = []
    for line in raw_lines:
        cleaned = clean_school_name(line)
        if cleaned and looks_like_school_line(cleaned):
            school_names.append(cleaned)
    school_names = list(dict.fromkeys(school_names))

    if not school_names:
        st.warning("Δεν αναγνωρίστηκε κανένα όνομα σχολείου στη λίστα.")
        st.stop()

    st.write(f"Βρέθηκαν **{len(school_names)}** πιθανά σχολεία. Αναζήτηση σε εξέλιξη...")
    progress = st.progress(0.0)
    status = st.empty()

    # ΣΗΜΑΝΤΙΚΟ: μόνο τα σχολεία που έγραψες παρακάτω θα εμφανιστούν στον χάρτη.
    results = []
    not_found = []
    for i, name in enumerate(school_names):
        status.write(f"Αναζήτηση: {name}")
        found = locate_school(name)
        if found:
            lat, lon, address, method, matched_name = found
            dist_km = geodesic(home_coords, (lat, lon)).km
            results.append({
                "Έγραψες": name,
                "Βρέθηκε ως": matched_name,
                "Απόσταση (χλμ)": round(dist_km, 2),
                "Διεύθυνση": address, "Πηγή": method,
                "_lat": lat, "_lon": lon,
            })
        else:
            not_found.append(name)
        progress.progress((i + 1) / len(school_names))
        time.sleep(0.2)

    status.empty()
    progress.empty()
    results.sort(key=lambda r: r["Απόσταση (χλμ)"])

    st.subheader("Αποτελέσματα (ταξινομημένα κατά απόσταση)")
    st.dataframe(
        [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
        use_container_width=True,
        hide_index=True,
    )

    if not_found:
        with st.expander(f"⚠ {len(not_found)} σχολεία δεν βρέθηκαν αυτόματα"):
            for n in not_found:
                st.write(f"- {n}")

    st.subheader("Διαδραστικός χάρτης")
    st.caption("Εμφανίζονται μόνο τα σχολεία της λίστας που επικόλλησες παραπάνω.")
    m = folium.Map(location=home_coords, zoom_start=12)
    folium.Marker(
        home_coords, popup="Το σπίτι μου", tooltip="Σπίτι",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)
    for r in results:
        folium.Marker(
            [r["_lat"], r["_lon"]],
            popup=folium.Popup(
                f"<b>{r['Βρέθηκε ως']}</b><br>{r['Απόσταση (χλμ)']} χλμ<br>{r['Διεύθυνση']}",
                max_width=300,
            ),
            tooltip=f"{r['Βρέθηκε ως']} ({r['Απόσταση (χλμ)']} χλμ)",
            icon=folium.Icon(color="blue", icon="graduation-cap", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=520, scrolling=True)
else:
    st.info("Συμπλήρωσε τη διεύθυνση και τη λίστα σχολείων, μετά πάτα το κουμπί.")
