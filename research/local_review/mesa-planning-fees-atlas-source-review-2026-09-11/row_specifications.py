"""Atlas visually checked source-line/column assignments, not a fee calculator."""
# table id, physical page, source heading, rows(start line,end line,first fee,second fee)
TABLES = [
('P1-GENERAL',1,'Application fees — general and Conditional Use',[
(12,12,'80.00','see Short Form'),(13,14,'80.00','0.00'),(15,16,'275.00','0.00'),(17,18,'10.00','0.00'),(19,20,'275.00','275.001'),(23,25,'525.00','0.00'),(26,27,'975.00','0.00'),(28,29,'half of original fee','0.00'),(30,31,'105.00','0.00'),(32,33,'80.00','0.00'),(34,35,'500.00','0.00')]),
('P1-MAJOR',1,'Major Subdivision',[(37,38,'225.00','0.00'),(39,41,'690.00','0.00'),(42,43,'620.00','0.00'),(44,45,'225.00','0.00')]),
('P1-MISC',1,'Minor Subdivision and Oil & Gas Drilling',[(46,47,'275.00','0.00'),(48,49,'80.00','0.00')]),
('P1-PUD',1,'Plan Unit Development (PUD)',[(51,52,'225.00','0.00'),(53,55,'665.00','0.00'),(56,57,'620.00','0.00'),(58,59,'225.00','0.00')]),
('P1-ACREAGE',1,'ACREAGE FEE CHART (All zones other than AFT Majors)',[(63,64,'140.00','0.00'),(65,66,'195.00','0.00'),(67,68,'255.00','0.00'),(69,70,'395.00','0.00'),(71,72,'560.00','0.00'),(73,74,'675.00','0.00'),(75,76,'675.00','0.00'),(77,78,'Fee Plus $55.00 per 25 acres','0.00')]),
('P1-PROPERTY',1,'Property Line Adjustments',[(81,82,'275.00','0.00'),(83,84,'275.00','0.00'),(85,86,'470.00','0.00')]),
('P1-LAST',1,'Other application fees',[(87,88,'10.00','0.00'),(89,90,'10.00','0.00'),(91,92,'500.00','0.00')]),
('P2-APPLICATIONS',2,'Application fees (continued)',[(2,4,'N/A','0.00'),(5,6,'10.00','0.00'),(7,8,'275.00','0.00'),(9,10,'275.00','0.00'),(11,12,'80.00','0.00'),(13,14,'155.00','0.00'),(15,16,'No Fee','No Fee'),(17,18,'445.00','0.00'),(19,20,'80.00','0.00'),(21,22,'300.00','0.00')]),
('P2-CONTINUATION',2,'CONTINUATION FEES',[(24,25,'$40.00**','$0.00'),(26,27,'$40.00**','$0.00**'),(28,31,'$.45*','$0.00*')]),
('P2-SCHOOL',2,'School Land Dedication Fee Per Residential Dwelling Unit',[(42,43,'$920.00',None),(44,44,'920.00',None),(45,45,'920.00',None),(46,46,'920.00',None)]),
('P2-TIF',2,'Transportation Impact Fee (TIF)',[(51,52,'$1902.00*',None)]),
('P2-COPIES',2,'Copies',[(55,55,'$.25',None),(56,56,'1.00',None),(57,57,'2.00',None),(58,58,'5.00',None)]),
('P2-PUBLICATIONS',2,'Publications',[(61,61,'$30.00',None),(62,62,'100.00',None),(63,63,'30.00',None),(64,64,'15.00',None),(65,65,'15.00',None),(66,66,'15.00',None),(67,67,'15.00',None),(68,68,'10.00',None)]),
('P3-GIS',3,'GIS Product Fee Schedule Plotting',[(4,4,'$5.00',None),(5,5,'5.00',None),(6,6,'8.00',None),(7,7,'$15.00',None),(8,8,'$5.00 Per Sheet',None)]),
('P3-IMAGERY',3,'Digital Imagery',[(17,18,'$10.00 per sm (No Minimum)',None),(19,20,'$25.00 per square mile. (2 square mile minimum $50.00 Minimum Charge)',None)]),
('P3-CGS',3,'Colorado Geological Survey (CGS) Review',[(27,29,'$600.00',None),(30,32,'$950.00',None),(33,35,'$1550.00',None),(36,38,'$2500.00',None)]),
('P3-RECORDING',3,'Recording Fees',[(40,40,None,None)])]
