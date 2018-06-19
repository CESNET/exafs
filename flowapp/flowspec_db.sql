-- MySQL dump 10.14  Distrib 5.5.56-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: flowspec
-- ------------------------------------------------------
-- Server version	5.5.56-MariaDB

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
-- Table structure for table `RTBH`
--

DROP TABLE IF EXISTS `RTBH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RTBH` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ipv4` varchar(255) DEFAULT NULL,
  `ipv4_mask` int(11) DEFAULT NULL,
  `ipv6` varchar(255) DEFAULT NULL,
  `ipv6_mask` int(11) DEFAULT NULL,
  `community` varchar(255) DEFAULT NULL,
  `comment` text,
  `expires` datetime DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `RTBH_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RTBH`
--

LOCK TABLES `RTBH` WRITE;
/*!40000 ALTER TABLE `RTBH` DISABLE KEYS */;
/*!40000 ALTER TABLE `RTBH` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `action`
--

DROP TABLE IF EXISTS `action`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `action` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(120) DEFAULT NULL,
  `command` varchar(120) DEFAULT NULL,
  `description` varchar(260) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `command` (`command`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `action`
--

LOCK TABLES `action` WRITE;
/*!40000 ALTER TABLE `action` DISABLE KEYS */;
INSERT INTO `action` VALUES (1,'QoS 0.1 Mbps','rate-limit 12800','QoS'),(2,'QoS 1 Mbps','rate-limit 13107200','QoS'),(3,'QoS 10 Mbps','rate-limit 131072000','QoS'),(5,'QoS 100 Mbps','rate-limit 1310720000','QoS'),(6,'QoS 500 Mbps','rate-limit 6553600000','QoS'),(7,'Discard','discard','Discard');
/*!40000 ALTER TABLE `action` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flowspec4`
--

DROP TABLE IF EXISTS `flowspec4`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flowspec4` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `source` varchar(255) DEFAULT NULL,
  `source_mask` int(11) DEFAULT NULL,
  `source_port` varchar(255) DEFAULT NULL,
  `dest` varchar(255) DEFAULT NULL,
  `dest_mask` int(11) DEFAULT NULL,
  `dest_port` varchar(255) DEFAULT NULL,
  `protocol` varchar(255) DEFAULT NULL,
  `flags` varchar(255) DEFAULT NULL,
  `packet_len` varchar(255) DEFAULT NULL,
  `comment` text,
  `expires` datetime DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `action_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `action_id` (`action_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `flowspec4_ibfk_1` FOREIGN KEY (`action_id`) REFERENCES `action` (`id`),
  CONSTRAINT `flowspec4_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flowspec4`
--

LOCK TABLES `flowspec4` WRITE;
/*!40000 ALTER TABLE `flowspec4` DISABLE KEYS */;
INSERT INTO `flowspec4` VALUES (3,'10.10.10.1',32,'','',NULL,'','tcp','','','','2017-11-01 18:08:00','2017-10-25 16:08:51',7,3),(10,'',NULL,'','147.230.16.234',32,'','tcp','','','','2017-11-28 21:20:00','2017-11-21 20:26:09',7,2);
/*!40000 ALTER TABLE `flowspec4` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flowspec6`
--

DROP TABLE IF EXISTS `flowspec6`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flowspec6` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `source` varchar(255) DEFAULT NULL,
  `source_mask` int(11) DEFAULT NULL,
  `source_port` varchar(255) DEFAULT NULL,
  `dest` varchar(255) DEFAULT NULL,
  `dest_mask` int(11) DEFAULT NULL,
  `dest_port` varchar(255) DEFAULT NULL,
  `next_header` varchar(255) DEFAULT NULL,
  `flags` varchar(255) DEFAULT NULL,
  `packet_len` varchar(255) DEFAULT NULL,
  `comment` text,
  `expires` datetime DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `action_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `action_id` (`action_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `flowspec6_ibfk_1` FOREIGN KEY (`action_id`) REFERENCES `action` (`id`),
  CONSTRAINT `flowspec6_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flowspec6`
--

LOCK TABLES `flowspec6` WRITE;
/*!40000 ALTER TABLE `flowspec6` DISABLE KEYS */;
/*!40000 ALTER TABLE `flowspec6` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `log`
--

DROP TABLE IF EXISTS `log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `time` datetime DEFAULT NULL,
  `task` varchar(20) DEFAULT NULL,
  `rule_type` int(11) DEFAULT NULL,
  `rule_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `log`
--

LOCK TABLES `log` WRITE;
/*!40000 ALTER TABLE `log` DISABLE KEYS */;
/*!40000 ALTER TABLE `log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organization`
--

DROP TABLE IF EXISTS `organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `organization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) DEFAULT NULL,
  `arange` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organization`
--

LOCK TABLES `organization` WRITE;
/*!40000 ALTER TABLE `organization` DISABLE KEYS */;
INSERT INTO `organization` VALUES (1,'TU Liberec','147.230.0.0/16\n2001:718:1c01::/48'),(2,'Cesnet','147.32.0.0/15\r\n147.228.0.0/14\r\n160.216.0.0/15\r\n146.102.0.0/16\r\n147.251.0.0/16\r\n158.194.0.0/16\r\n158.196.0.0/16\r\n193.84.32.0/20\r\n193.84.160.0/20\r\n193.84.192.0/19\r\n195.113.0.0/16\r\n195.178.64.0/19\r\n78.128.128.0/17\r\n2001:718::/29'),(4,'IT4Innovations','195.113.250.0/24\r\n2001:718:1007::/48'),(5,'VŠB-TU Ostrava','195.113.113.0/24');
/*!40000 ALTER TABLE `organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role`
--

DROP TABLE IF EXISTS `role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `role` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) DEFAULT NULL,
  `description` varchar(260) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role`
--

LOCK TABLES `role` WRITE;
/*!40000 ALTER TABLE `role` DISABLE KEYS */;
INSERT INTO `role` VALUES (1,'view','just view, no edit'),(2,'user','can edit'),(3,'admin','admin');
/*!40000 ALTER TABLE `role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (3,'adamec@cesnet.cz'),(7,'bodik@cesnet.cz'),(1,'jiri.vrany@tul.cz'),(6,'kostenec@cesnet.cz'),(5,'kuba@cesnet.cz'),(2,'petr.adamec@tul.cz'),(4,'ver10@cesnet.cz');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_organization`
--

DROP TABLE IF EXISTS `user_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_organization` (
  `user_id` int(11) NOT NULL,
  `organization_id` int(11) NOT NULL,
  PRIMARY KEY (`user_id`,`organization_id`),
  KEY `organization_id` (`organization_id`),
  CONSTRAINT `user_organization_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `user_organization_ibfk_2` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_organization`
--

LOCK TABLES `user_organization` WRITE;
/*!40000 ALTER TABLE `user_organization` DISABLE KEYS */;
INSERT INTO `user_organization` VALUES (1,1),(2,1),(2,2),(3,2),(4,1),(4,2),(5,2),(6,2),(7,2);
/*!40000 ALTER TABLE `user_organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_role`
--

DROP TABLE IF EXISTS `user_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_role` (
  `user_id` int(11) NOT NULL,
  `role_id` int(11) NOT NULL,
  PRIMARY KEY (`user_id`,`role_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `user_role_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `user_role_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_role`
--

LOCK TABLES `user_role` WRITE;
/*!40000 ALTER TABLE `user_role` DISABLE KEYS */;
INSERT INTO `user_role` VALUES (1,3),(2,3),(3,3),(4,3),(5,3),(6,2),(7,2);
/*!40000 ALTER TABLE `user_role` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-11-22  9:56:29
