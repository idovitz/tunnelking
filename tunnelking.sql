-- phpMyAdmin SQL Dump
-- version 2.11.3deb1ubuntu1.2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generatie Tijd: 08 Sept 2009 om 15:13
-- Server versie: 5.0.51
-- PHP Versie: 5.2.4-2ubuntu5.6

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `tunnelking`
--

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `apps_users`
--

CREATE TABLE IF NOT EXISTS `apps_users` (
  `appname` varchar(255) collate utf8_unicode_ci NOT NULL,
  `userid` varchar(8) collate utf8_unicode_ci NOT NULL,
  `autostart` tinyint(1) default NULL,
  PRIMARY KEY  (`appname`,`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `configurations`
--

CREATE TABLE IF NOT EXISTS `configurations` (
  `id` tinyint(2) NOT NULL auto_increment,
  `name` varchar(255) collate utf8_unicode_ci NOT NULL,
  `dn` varchar(255) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=34 ;

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `keys`
--

CREATE TABLE IF NOT EXISTS `keys` (
  `id` bigint(8) NOT NULL auto_increment,
  `userid` int(8) NOT NULL,
  `key` varchar(10) collate utf8_unicode_ci NOT NULL,
  `expiretime` datetime NOT NULL,
  `ip` varchar(15) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=28 ;

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `options`
--

CREATE TABLE IF NOT EXISTS `options` (
  `id` smallint(7) NOT NULL auto_increment,
  `type` varchar(1) collate utf8_unicode_ci NOT NULL,
  `confid` tinyint(2) NOT NULL,
  `name` varchar(255) collate utf8_unicode_ci NOT NULL,
  `value` text collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `confid` (`confid`),
  KEY `name` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1617 ;

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `ssl`
--

CREATE TABLE IF NOT EXISTS `ssl` (
  `cn` varchar(255) collate utf8_unicode_ci NOT NULL,
  `confid` tinyint(2) NOT NULL,
  `type` varchar(6) collate utf8_unicode_ci NOT NULL,
  `pem` text collate utf8_unicode_ci NOT NULL,
  `serial` varchar(65) collate utf8_unicode_ci default NULL,
  PRIMARY KEY  (`cn`,`type`,`confid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Tabel structuur voor tabel `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(8) NOT NULL auto_increment,
  `confid` tinyint(2) NOT NULL,
  `name` varchar(255) collate utf8_unicode_ci NOT NULL,
  `keypin` varchar(50) collate utf8_unicode_ci default NULL,
  `password` varchar(255) collate utf8_unicode_ci default NULL,
  `otpRecipient` varchar(255) collate utf8_unicode_ci default NULL,
  `lastlogin` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `confid` (`confid`,`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=51 ;
