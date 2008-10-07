-- MySQL dump 10.11
--
-- Host: localhost    Database: fpdb
-- ------------------------------------------------------
-- Server version	5.0.54-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `autorates`
--

DROP TABLE IF EXISTS `autorates`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `autorates` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `player_id` int(10) unsigned default NULL,
  `gametype_id` smallint(5) unsigned default NULL,
  `description` varchar(50) default NULL,
  `short_desc` char(8) default NULL,
  `rating_time` datetime default NULL,
  `hand_count` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `player_id` (`player_id`),
  KEY `gametype_id` (`gametype_id`),
  CONSTRAINT `autorates_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`),
  CONSTRAINT `autorates_ibfk_2` FOREIGN KEY (`gametype_id`) REFERENCES `gametypes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `autorates`
--

LOCK TABLES `autorates` WRITE;
/*!40000 ALTER TABLE `autorates` DISABLE KEYS */;
/*!40000 ALTER TABLE `autorates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `board_cards`
--

DROP TABLE IF EXISTS `board_cards`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `board_cards` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `hand_id` bigint(20) unsigned default NULL,
  `card1_value` smallint(6) default NULL,
  `card1_suit` char(1) default NULL,
  `card2_value` smallint(6) default NULL,
  `card2_suit` char(1) default NULL,
  `card3_value` smallint(6) default NULL,
  `card3_suit` char(1) default NULL,
  `card4_value` smallint(6) default NULL,
  `card4_suit` char(1) default NULL,
  `card5_value` smallint(6) default NULL,
  `card5_suit` char(1) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `hand_id` (`hand_id`),
  CONSTRAINT `board_cards_ibfk_1` FOREIGN KEY (`hand_id`) REFERENCES `hands` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `board_cards`
--

LOCK TABLES `board_cards` WRITE;
/*!40000 ALTER TABLE `board_cards` DISABLE KEYS */;
INSERT INTO `board_cards` VALUES (1,1,12,'d',10,'h',11,'s',2,'s',7,'s'),(2,2,10,'h',11,'d',3,'c',7,'c',4,'s'),(3,3,4,'h',9,'s',14,'d',12,'c',13,'s'),(4,5,4,'s',13,'c',8,'s',6,'s',12,'c'),(5,6,11,'c',4,'c',13,'c',7,'h',8,'s'),(6,7,0,'x',0,'x',0,'x',0,'x',0,'x'),(7,8,10,'c',9,'s',7,'h',0,'x',0,'x'),(8,9,11,'d',10,'d',2,'c',14,'s',8,'s');
/*!40000 ALTER TABLE `board_cards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gametypes`
--

DROP TABLE IF EXISTS `gametypes`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `gametypes` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `site_id` smallint(5) unsigned default NULL,
  `type` char(4) default NULL,
  `category` varchar(9) default NULL,
  `limit_type` char(2) default NULL,
  `max_seats` smallint(6) default NULL,
  `small_blind` int(11) default NULL,
  `big_blind` int(11) default NULL,
  `small_bet` int(11) default NULL,
  `big_bet` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `site_id` (`site_id`),
  CONSTRAINT `gametypes_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `gametypes`
--

LOCK TABLES `gametypes` WRITE;
/*!40000 ALTER TABLE `gametypes` DISABLE KEYS */;
INSERT INTO `gametypes` VALUES (1,1,'ring','holdem','fl',10,10,25,25,50),(2,1,'ring','holdem','fl',10,25,50,50,100),(3,1,'ring','holdem','fl',10,50,100,100,200),(4,1,'ring','holdem','fl',10,100,200,200,400),(5,1,'ring','holdem','fl',10,150,300,300,600),(6,1,'ring','holdem','fl',10,250,500,500,1000),(7,1,'ring','holdem','fl',10,400,800,800,1600),(8,1,'ring','holdem','fl',10,500,1000,1000,2000),(9,1,'ring','holdem','fl',10,1000,1500,1500,3000),(10,1,'ring','holdem','fl',10,1500,3000,3000,6000),(11,1,'ring','omahahi','pl',10,5,10,0,0),(12,1,'ring','omahahi','pl',10,10,25,0,0),(13,1,'ring','omahahi','pl',10,25,50,0,0),(14,1,'ring','omahahi','pl',10,50,100,0,0),(15,1,'ring','omahahi','pl',10,100,200,0,0),(16,1,'ring','omahahi','pl',10,200,400,0,0),(17,1,'ring','omahahi','pl',10,1000,2000,0,0),(18,1,'ring','omahahi','cp',10,2500,5000,0,0),(19,1,'ring','omahahilo','fl',10,10,25,25,50),(20,1,'ring','omahahilo','fl',10,50,100,100,200),(21,1,'ring','omahahilo','fl',10,150,300,300,600),(22,1,'ring','omahahilo','fl',10,250,500,500,1000),(23,1,'ring','omahahilo','pl',10,10,25,0,0),(24,1,'ring','omahahilo','pl',10,50,100,0,0),(25,1,'ring','omahahilo','pl',10,100,200,0,0),(26,1,'ring','omahahilo','nl',10,5,10,0,0),(27,1,'ring','omahahilo','nl',10,50,100,0,0),(28,1,'ring','omahahilo','nl',10,100,200,0,0),(29,1,'ring','razz','fl',8,0,0,25,50),(30,1,'ring','razz','fl',8,0,0,50,100),(31,1,'ring','razz','fl',8,0,0,100,200),(32,1,'ring','razz','fl',8,0,0,200,400),(33,1,'ring','razz','fl',8,0,0,300,600),(34,1,'ring','razz','fl',8,0,0,500,1000),(35,1,'ring','razz','fl',8,0,0,800,1600),(36,1,'ring','razz','fl',8,0,0,1500,3000),(37,1,'ring','razz','fl',8,0,0,2000,4000),(38,1,'ring','razz','fl',8,0,0,3000,6000),(39,1,'ring','razz','fl',8,0,0,10000,20000),(40,1,'ring','studhi','fl',8,0,0,25,50),(41,1,'ring','studhi','fl',8,0,0,200,400),(42,1,'ring','studhi','fl',8,0,0,300,600),(43,1,'ring','studhi','fl',8,0,0,500,1000),(44,1,'ring','studhilo','fl',8,0,0,50,100),(45,1,'ring','studhilo','fl',8,0,0,100,200),(46,1,'ring','studhilo','fl',8,0,0,1500,3000),(47,2,'ring','holdem','fl',10,1,2,2,4),(48,2,'ring','holdem','fl',10,2,5,5,10),(49,2,'ring','holdem','fl',10,5,10,10,20),(50,2,'ring','holdem','fl',10,10,25,25,50),(51,2,'ring','holdem','nl',10,1,2,0,0),(52,2,'ring','holdem','nl',10,2,5,0,0),(53,2,'ring','holdem','nl',10,5,10,0,0),(54,2,'ring','omahahi','pl',10,1,2,0,0),(55,2,'ring','omahahi','pl',10,10,25,0,0),(56,2,'ring','omahahilo','fl',10,1,2,2,4),(57,2,'ring','omahahilo','pl',10,1,2,0,0),(58,2,'ring','razz','fl',8,0,0,50,100),(59,2,'tour','razz','fl',8,0,0,10,20),(60,2,'ring','studhi','fl',8,0,0,4,8),(61,2,'ring','studhi','fl',8,0,0,10,20),(62,2,'ring','studhilo','fl',8,0,0,4,8),(63,2,'ring','studhilo','fl',8,0,0,10,20),(64,2,'ring','studhilo','fl',8,0,0,25,50),(65,2,'ring','studhilo','fl',8,0,0,50,100);
/*!40000 ALTER TABLE `gametypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hands`
--

DROP TABLE IF EXISTS `hands`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `hands` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `site_hand_no` bigint(20) default NULL,
  `gametype_id` smallint(5) unsigned default NULL,
  `hand_start` datetime default NULL,
  `seats` smallint(6) default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `gametype_id` (`gametype_id`),
  CONSTRAINT `hands_ibfk_1` FOREIGN KEY (`gametype_id`) REFERENCES `gametypes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `hands`
--

LOCK TABLES `hands` WRITE;
/*!40000 ALTER TABLE `hands` DISABLE KEYS */;
INSERT INTO `hands` VALUES (1,14519394979,47,'2008-01-13 05:22:15',7,NULL,NULL),(2,14519420999,47,'2008-01-13 05:23:43',7,NULL,NULL),(3,14519433154,47,'2008-01-13 05:24:25',7,NULL,NULL),(4,6367428246,46,'2008-05-11 04:47:38',4,NULL,NULL),(5,6929537410,14,'2008-06-22 22:15:44',9,NULL,NULL),(6,6929553738,14,'2008-06-22 22:17:06',9,NULL,NULL),(7,6929572212,14,'2008-06-22 22:18:40',8,NULL,NULL),(8,6929576743,14,'2008-06-22 22:19:03',8,NULL,NULL),(9,6929587483,14,'2008-06-22 22:19:57',8,NULL,NULL);
/*!40000 ALTER TABLE `hands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hands_actions`
--

DROP TABLE IF EXISTS `hands_actions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `hands_actions` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `hand_player_id` bigint(20) unsigned default NULL,
  `street` smallint(6) default NULL,
  `action_no` smallint(6) default NULL,
  `action` char(5) default NULL,
  `amount` int(11) default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `hand_player_id` (`hand_player_id`),
  CONSTRAINT `hands_actions_ibfk_1` FOREIGN KEY (`hand_player_id`) REFERENCES `hands_players` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=181 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `hands_actions`
--

LOCK TABLES `hands_actions` WRITE;
/*!40000 ALTER TABLE `hands_actions` DISABLE KEYS */;
INSERT INTO `hands_actions` VALUES (1,1,0,0,'call',4,NULL,NULL),(2,2,0,0,'blind',1,NULL,NULL),(3,2,0,1,'call',3,NULL,NULL),(4,3,0,0,'blind',2,NULL,NULL),(5,3,0,1,'fold',0,NULL,NULL),(6,4,0,0,'bet',4,NULL,NULL),(7,5,0,0,'fold',0,NULL,NULL),(8,6,0,0,'fold',0,NULL,NULL),(9,7,0,0,'fold',0,NULL,NULL),(10,1,1,0,'call',2,NULL,NULL),(11,2,1,0,'check',0,NULL,NULL),(12,2,1,1,'call',2,NULL,NULL),(13,4,1,0,'bet',2,NULL,NULL),(14,1,2,0,'call',4,NULL,NULL),(15,2,2,0,'check',0,NULL,NULL),(16,2,2,1,'call',4,NULL,NULL),(17,4,2,0,'bet',4,NULL,NULL),(18,1,3,0,'fold',0,NULL,NULL),(19,2,3,0,'check',0,NULL,NULL),(20,2,3,1,'fold',0,NULL,NULL),(21,4,3,0,'bet',4,NULL,NULL),(22,8,0,0,'fold',0,NULL,NULL),(23,9,0,0,'call',2,NULL,NULL),(24,10,0,0,'fold',0,NULL,NULL),(25,11,0,0,'blind',1,NULL,NULL),(26,11,0,1,'call',1,NULL,NULL),(27,12,0,0,'blind',2,NULL,NULL),(28,12,0,1,'check',0,NULL,NULL),(29,13,0,0,'fold',0,NULL,NULL),(30,14,0,0,'fold',0,NULL,NULL),(31,9,1,0,'call',2,NULL,NULL),(32,11,1,0,'check',0,NULL,NULL),(33,11,1,1,'call',2,NULL,NULL),(34,12,1,0,'bet',2,NULL,NULL),(35,9,2,0,'bet',8,NULL,NULL),(36,11,2,0,'check',0,NULL,NULL),(37,11,2,1,'fold',0,NULL,NULL),(38,12,2,0,'bet',4,NULL,NULL),(39,12,2,1,'call',4,NULL,NULL),(40,9,3,0,'bet',4,NULL,NULL),(41,12,3,0,'check',0,NULL,NULL),(42,12,3,1,'call',4,NULL,NULL),(43,15,0,0,'fold',0,NULL,NULL),(44,16,0,0,'fold',0,NULL,NULL),(45,17,0,0,'call',2,NULL,NULL),(46,17,0,1,'call',2,NULL,NULL),(47,18,0,0,'call',2,NULL,NULL),(48,18,0,1,'call',2,NULL,NULL),(49,19,0,0,'blind',1,NULL,NULL),(50,19,0,1,'bet',3,NULL,NULL),(51,20,0,0,'blind',2,NULL,NULL),(52,20,0,1,'call',2,NULL,NULL),(53,21,0,0,'fold',0,NULL,NULL),(54,17,1,0,'bet',2,NULL,NULL),(55,17,1,1,'bet',4,NULL,NULL),(56,17,1,2,'call',2,NULL,NULL),(57,18,1,0,'bet',4,NULL,NULL),(58,18,1,1,'bet',4,NULL,NULL),(59,19,1,0,'check',0,NULL,NULL),(60,19,1,1,'fold',0,NULL,NULL),(61,20,1,0,'check',0,NULL,NULL),(62,20,1,1,'fold',0,NULL,NULL),(63,17,2,0,'bet',4,NULL,NULL),(64,17,2,1,'bet',8,NULL,NULL),(65,17,2,2,'call',4,NULL,NULL),(66,18,2,0,'bet',8,NULL,NULL),(67,18,2,1,'bet',8,NULL,NULL),(68,17,3,0,'bet',4,NULL,NULL),(69,17,3,1,'bet',8,NULL,NULL),(70,17,3,2,'call',4,NULL,NULL),(71,18,3,0,'bet',8,NULL,NULL),(72,18,3,1,'bet',8,NULL,NULL),(73,22,3,0,'blind',500,NULL,NULL),(74,22,3,1,'call',1000,NULL,NULL),(75,23,3,0,'fold',0,NULL,NULL),(76,24,3,0,'bet',1500,NULL,NULL),(77,25,3,0,'fold',0,NULL,NULL),(78,22,4,0,'call',1500,NULL,NULL),(79,24,4,0,'bet',1500,NULL,NULL),(80,22,5,0,'call',3000,NULL,NULL),(81,24,5,0,'bet',3000,NULL,NULL),(82,22,6,0,'bet',3000,NULL,NULL),(83,24,6,0,'call',3000,NULL,NULL),(84,22,7,0,'bet',3000,NULL,NULL),(85,24,7,0,'call',3000,NULL,NULL),(86,26,0,0,'blind',100,NULL,NULL),(87,26,0,1,'check',0,NULL,NULL),(88,27,0,0,'fold',0,NULL,NULL),(89,28,0,0,'fold',0,NULL,NULL),(90,29,0,0,'fold',0,NULL,NULL),(91,30,0,0,'fold',0,NULL,NULL),(92,31,0,0,'fold',0,NULL,NULL),(93,32,0,0,'blind',100,NULL,NULL),(94,32,0,1,'check',0,NULL,NULL),(95,33,0,0,'call',100,NULL,NULL),(96,34,0,0,'blind',50,NULL,NULL),(97,34,0,1,'call',50,NULL,NULL),(98,26,1,0,'check',0,NULL,NULL),(99,32,1,0,'check',0,NULL,NULL),(100,33,1,0,'check',0,NULL,NULL),(101,34,1,0,'check',0,NULL,NULL),(102,26,2,0,'check',0,NULL,NULL),(103,26,2,1,'fold',0,NULL,NULL),(104,32,2,0,'check',0,NULL,NULL),(105,32,2,1,'fold',0,NULL,NULL),(106,33,2,0,'bet',400,NULL,NULL),(107,34,2,0,'check',0,NULL,NULL),(108,34,2,1,'call',400,NULL,NULL),(109,33,3,0,'check',0,NULL,NULL),(110,34,3,0,'check',0,NULL,NULL),(111,35,0,0,'blind',50,NULL,NULL),(112,35,0,1,'call',150,NULL,NULL),(113,36,0,0,'blind',100,NULL,NULL),(114,36,0,1,'call',100,NULL,NULL),(115,37,0,0,'fold',0,NULL,NULL),(116,38,0,0,'bet',200,NULL,NULL),(117,39,0,0,'fold',0,NULL,NULL),(118,40,0,0,'call',200,NULL,NULL),(119,41,0,0,'fold',0,NULL,NULL),(120,42,0,0,'fold',0,NULL,NULL),(121,43,0,0,'fold',0,NULL,NULL),(122,35,1,0,'check',0,NULL,NULL),(123,36,1,0,'check',0,NULL,NULL),(124,38,1,0,'check',0,NULL,NULL),(125,40,1,0,'check',0,NULL,NULL),(126,35,2,0,'check',0,NULL,NULL),(127,35,2,1,'fold',0,NULL,NULL),(128,36,2,0,'check',0,NULL,NULL),(129,36,2,1,'call',350,NULL,NULL),(130,38,2,0,'bet',350,NULL,NULL),(131,40,2,0,'fold',0,NULL,NULL),(132,36,3,0,'check',0,NULL,NULL),(133,36,3,1,'call',1000,NULL,NULL),(134,38,3,0,'bet',1000,NULL,NULL),(135,44,0,0,'bet',200,NULL,NULL),(136,44,0,1,'unbet',100,NULL,NULL),(137,45,0,0,'blind',50,NULL,NULL),(138,45,0,1,'fold',0,NULL,NULL),(139,46,0,0,'blind',100,NULL,NULL),(140,46,0,1,'fold',0,NULL,NULL),(141,47,0,0,'fold',0,NULL,NULL),(142,48,0,0,'fold',0,NULL,NULL),(143,49,0,0,'fold',0,NULL,NULL),(144,50,0,0,'fold',0,NULL,NULL),(145,51,0,0,'fold',0,NULL,NULL),(146,52,0,0,'bet',400,NULL,NULL),(147,53,0,0,'fold',0,NULL,NULL),(148,54,0,0,'blind',50,NULL,NULL),(149,54,0,1,'fold',0,NULL,NULL),(150,55,0,0,'blind',100,NULL,NULL),(151,55,0,1,'fold',0,NULL,NULL),(152,56,0,0,'call',100,NULL,NULL),(153,56,0,1,'fold',0,NULL,NULL),(154,57,0,0,'fold',0,NULL,NULL),(155,58,0,0,'call',100,NULL,NULL),(156,58,0,1,'fold',0,NULL,NULL),(157,59,0,0,'call',100,NULL,NULL),(158,59,0,1,'call',300,NULL,NULL),(159,52,1,0,'bet',800,NULL,NULL),(160,52,1,1,'unbet',800,NULL,NULL),(161,59,1,0,'check',0,NULL,NULL),(162,59,1,1,'fold',0,NULL,NULL),(163,60,0,0,'fold',0,NULL,NULL),(164,61,0,0,'fold',0,NULL,NULL),(165,62,0,0,'blind',50,NULL,NULL),(166,62,0,1,'call',50,NULL,NULL),(167,63,0,0,'blind',100,NULL,NULL),(168,63,0,1,'check',0,NULL,NULL),(169,64,0,0,'fold',0,NULL,NULL),(170,65,0,0,'fold',0,NULL,NULL),(171,66,0,0,'call',100,NULL,NULL),(172,67,0,0,'call',100,NULL,NULL),(173,62,1,0,'bet',300,NULL,NULL),(174,62,1,1,'bet',3400,NULL,NULL),(175,62,1,2,'bet',15230,NULL,NULL),(176,63,1,0,'fold',0,NULL,NULL),(177,66,1,0,'fold',0,NULL,NULL),(178,67,1,0,'bet',1100,NULL,NULL),(179,67,1,1,'bet',10400,NULL,NULL),(180,67,1,2,'call',3730,NULL,NULL);
/*!40000 ALTER TABLE `hands_actions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hands_players`
--

DROP TABLE IF EXISTS `hands_players`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `hands_players` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `hand_id` bigint(20) unsigned default NULL,
  `player_id` int(10) unsigned default NULL,
  `player_startcash` int(11) default NULL,
  `position` char(1) default NULL,
  `ante` int(11) default NULL,
  `card1_value` smallint(6) default NULL,
  `card1_suit` char(1) default NULL,
  `card2_value` smallint(6) default NULL,
  `card2_suit` char(1) default NULL,
  `card3_value` smallint(6) default NULL,
  `card3_suit` char(1) default NULL,
  `card4_value` smallint(6) default NULL,
  `card4_suit` char(1) default NULL,
  `card5_value` smallint(6) default NULL,
  `card5_suit` char(1) default NULL,
  `card6_value` smallint(6) default NULL,
  `card6_suit` char(1) default NULL,
  `card7_value` smallint(6) default NULL,
  `card7_suit` char(1) default NULL,
  `winnings` int(11) default NULL,
  `rake` int(11) default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  `tourneys_players_id` bigint(20) unsigned default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `hand_id` (`hand_id`),
  KEY `player_id` (`player_id`),
  KEY `tourneys_players_id` (`tourneys_players_id`),
  CONSTRAINT `hands_players_ibfk_1` FOREIGN KEY (`hand_id`) REFERENCES `hands` (`id`),
  CONSTRAINT `hands_players_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`),
  CONSTRAINT `hands_players_ibfk_3` FOREIGN KEY (`tourneys_players_id`) REFERENCES `tourneys_players` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `hands_players`
--

LOCK TABLES `hands_players` WRITE;
/*!40000 ALTER TABLE `hands_players` DISABLE KEYS */;
INSERT INTO `hands_players` VALUES (1,1,1,75,'0',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(2,1,2,59,'S',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(3,1,3,147,'B',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(4,1,4,198,'4',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,31,1,NULL,NULL,NULL),(5,1,5,122,'3',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(6,1,6,48,'2',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(7,1,7,139,'1',NULL,10,'s',11,'h',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(8,2,1,65,'2',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(9,2,2,49,'1',NULL,8,'s',9,'s',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,35,1,NULL,NULL,NULL),(10,2,3,179,'0',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(11,2,4,205,'S',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(12,2,5,118,'B',NULL,12,'h',11,'s',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(13,2,6,34,'4',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(14,2,7,135,'3',NULL,8,'d',5,'d',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(15,3,1,65,'3',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(16,3,2,68,'2',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(17,3,3,179,'1',NULL,14,'h',9,'d',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,92,4,NULL,NULL,NULL),(18,3,4,201,'0',NULL,14,'c',10,'d',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(19,3,5,102,'S',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(20,3,6,34,'B',NULL,0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(21,3,7,135,'4',NULL,7,'c',11,'h',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(22,4,8,30350,NULL,300,5,'c',4,'h',2,'s',6,'c',14,'c',2,'c',2,'h',25000,200,NULL,NULL,NULL),(23,4,9,16400,NULL,300,0,'x',0,'x',3,'c',0,'x',0,'x',0,'x',0,'x',0,0,NULL,NULL,NULL),(24,4,10,91250,NULL,300,0,'x',0,'x',8,'c',5,'h',14,'h',11,'d',0,'x',0,0,NULL,NULL,NULL),(25,4,11,53150,NULL,300,0,'x',0,'x',11,'c',0,'x',0,'x',0,'x',0,'x',0,0,NULL,NULL,NULL),(26,5,12,9490,'B',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(27,5,13,14700,'6',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(28,5,14,6280,'5',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(29,5,15,13655,'4',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(30,5,16,5605,'3',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(31,5,17,25295,'2',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(32,5,18,20000,'1',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(33,5,19,16250,'0',NULL,10,'d',5,'s',3,'d',11,'s',NULL,NULL,NULL,NULL,NULL,NULL,1140,60,NULL,NULL,NULL),(34,5,20,27070,'S',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(35,6,12,9390,'S',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(36,6,21,10000,'B',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(37,6,14,6280,'6',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(38,6,15,13655,'5',NULL,4,'s',10,'c',14,'s',14,'c',NULL,NULL,NULL,NULL,NULL,NULL,3325,175,NULL,NULL,NULL),(39,6,16,5605,'4',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(40,6,17,25295,'3',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(41,6,18,19900,'2',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(42,6,19,16890,'1',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(43,6,20,26570,'0',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(44,7,12,9190,'0',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,250,0,NULL,NULL,NULL),(45,7,21,8450,'S',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(46,7,14,6280,'B',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(47,7,15,15430,'5',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(48,7,17,25095,'4',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(49,7,18,19900,'3',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(50,7,19,16890,'2',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(51,7,20,26570,'1',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(52,8,12,9340,'1',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,1095,55,NULL,NULL,NULL),(53,8,21,8400,'0',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(54,8,14,6180,'S',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(55,8,15,15430,'B',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(56,8,17,25095,'5',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(57,8,18,19900,'4',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(58,8,19,16890,'3',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(59,8,20,26570,'2',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(60,9,12,10035,'1',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(61,9,14,6130,'0',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(62,9,15,15330,'S',NULL,11,'c',11,'h',7,'s',5,'h',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(63,9,22,5000,'B',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(64,9,17,24995,'5',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(65,9,18,19900,'4',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(66,9,19,16790,'3',NULL,0,'x',0,'x',0,'x',0,'x',NULL,NULL,NULL,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(67,9,20,26170,'2',NULL,13,'h',14,'d',6,'h',12,'d',NULL,NULL,NULL,NULL,NULL,NULL,30560,300,NULL,NULL,NULL);
/*!40000 ALTER TABLE `hands_players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `players`
--

DROP TABLE IF EXISTS `players`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `players` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `name` varchar(32) default NULL,
  `site_id` smallint(5) unsigned default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `site_id` (`site_id`),
  CONSTRAINT `players_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `players`
--

LOCK TABLES `players` WRITE;
/*!40000 ALTER TABLE `players` DISABLE KEYS */;
INSERT INTO `players` VALUES (1,'Player_1',2,NULL,NULL),(2,'Player_2',2,NULL,NULL),(3,'Player_3',2,NULL,NULL),(4,'Player_4',2,NULL,NULL),(5,'Player_5',2,NULL,NULL),(6,'Player_6',2,NULL,NULL),(7,'Player_7',2,NULL,NULL),(8,'Play er9',1,NULL,NULL),(9,'Player_11',1,NULL,NULL),(10,'Player13',1,NULL,NULL),(11,'Player15',1,NULL,NULL),(12,'player16',1,NULL,NULL),(13,'player25',1,NULL,NULL),(14,'player18',1,NULL,NULL),(15,'player19',1,NULL,NULL),(16,'play-er26',1,NULL,NULL),(17,'player21',1,NULL,NULL),(18,'player22',1,NULL,NULL),(19,'player23',1,NULL,NULL),(20,'player24',1,NULL,NULL),(21,'player17',1,NULL,NULL),(22,'player20',1,NULL,NULL);
/*!40000 ALTER TABLE `players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `sites` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `name` varchar(32) default NULL,
  `currency` char(3) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `sites`
--

LOCK TABLES `sites` WRITE;
/*!40000 ALTER TABLE `sites` DISABLE KEYS */;
INSERT INTO `sites` VALUES (1,'Full Tilt Poker','USD'),(2,'PokerStars','USD');
/*!40000 ALTER TABLE `sites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tourneys`
--

DROP TABLE IF EXISTS `tourneys`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `tourneys` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `gametype_id` smallint(5) unsigned default NULL,
  `site_tourney_no` bigint(20) default NULL,
  `buyin` int(11) default NULL,
  `fee` int(11) default NULL,
  `knockout` int(11) default NULL,
  `entries` int(11) default NULL,
  `prizepool` int(11) default NULL,
  `start_time` datetime default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `gametype_id` (`gametype_id`),
  CONSTRAINT `tourneys_ibfk_1` FOREIGN KEY (`gametype_id`) REFERENCES `gametypes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `tourneys`
--

LOCK TABLES `tourneys` WRITE;
/*!40000 ALTER TABLE `tourneys` DISABLE KEYS */;
/*!40000 ALTER TABLE `tourneys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tourneys_players`
--

DROP TABLE IF EXISTS `tourneys_players`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `tourneys_players` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `tourney_id` int(10) unsigned default NULL,
  `player_id` int(10) unsigned default NULL,
  `payin_amount` int(11) default NULL,
  `rank` int(11) default NULL,
  `winnings` int(11) default NULL,
  `comment` text,
  `comment_ts` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `tourney_id` (`tourney_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `tourneys_players_ibfk_1` FOREIGN KEY (`tourney_id`) REFERENCES `tourneys` (`id`),
  CONSTRAINT `tourneys_players_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `tourneys_players`
--

LOCK TABLES `tourneys_players` WRITE;
/*!40000 ALTER TABLE `tourneys_players` DISABLE KEYS */;
/*!40000 ALTER TABLE `tourneys_players` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2008-07-12 18:42:27
