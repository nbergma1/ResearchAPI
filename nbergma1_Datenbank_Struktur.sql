-- phpMyAdmin SQL Dump
-- version 5.2.1deb1+deb12u1
-- https://www.phpmyadmin.net/
--
-- Host: wdb2.hs-mittweida.de:3306
-- Erstellungszeit: 25. Feb 2026 um 11:37
-- Server-Version: 10.11.14-MariaDB-0+deb12u2
-- PHP-Version: 8.2.29

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `nbergma1`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `comments`
--

CREATE TABLE `comments` (
  `id` bigint(20) NOT NULL,
  `video_id` bigint(20) DEFAULT NULL,
  `parent_comment_id` bigint(20) DEFAULT NULL,
  `text` text DEFAULT NULL,
  `like_count` bigint(20) DEFAULT NULL,
  `reply_count` text DEFAULT NULL,
  `create_time` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `follower`
--

CREATE TABLE `follower` (
  `username` varchar(45) NOT NULL,
  `display_name` varchar(45) DEFAULT NULL,
  `request_time` varchar(45) DEFAULT NULL,
  `request_username` varchar(45) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `following`
--

CREATE TABLE `following` (
  `username` varchar(45) NOT NULL,
  `request_username` varchar(45) NOT NULL,
  `request_time` datetime DEFAULT NULL,
  `display_name` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `playlist`
--

CREATE TABLE `playlist` (
  `playlist_id` varchar(45) NOT NULL,
  `playlist_item_total` varchar(45) DEFAULT NULL,
  `playlist_last_updated` int(11) DEFAULT NULL,
  `playlist_name` varchar(45) DEFAULT NULL,
  `playlist_video_ids` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `user`
--

CREATE TABLE `user` (
  `code` int(11) DEFAULT NULL,
  `verified` tinyint(1) DEFAULT NULL,
  `username` varchar(45) NOT NULL,
  `display_name` varchar(45) DEFAULT NULL,
  `avatar_url` text DEFAULT NULL,
  `follower_count` int(10) UNSIGNED DEFAULT NULL,
  `following_count` int(10) UNSIGNED DEFAULT NULL,
  `likes_count` int(10) UNSIGNED DEFAULT NULL,
  `video_count` int(10) UNSIGNED DEFAULT NULL,
  `bio_url` text DEFAULT NULL,
  `bio_description` varchar(100) DEFAULT NULL,
  `videos_id` int(10) UNSIGNED DEFAULT NULL,
  `playlist_playlist_id` varchar(45) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  `log_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `videos`
--

CREATE TABLE `videos` (
  `id` bigint(20) NOT NULL,
  `username` text DEFAULT NULL,
  `video_description` text DEFAULT NULL,
  `voice_to_text` text DEFAULT NULL,
  `video_tag` text DEFAULT NULL,
  `comment_count` bigint(20) DEFAULT NULL,
  `share_count` bigint(20) DEFAULT NULL,
  `region_code` text DEFAULT NULL,
  `playlist_id` text DEFAULT NULL,
  `view_count` bigint(20) DEFAULT NULL,
  `like_count` bigint(20) DEFAULT NULL,
  `music_id` bigint(20) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `hashtag_names` text DEFAULT NULL,
  `favorites_count` bigint(20) DEFAULT NULL,
  `hashtag_info_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`hashtag_info_list`)),
  `effect_ids` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect_ids`)),
  `effect_info_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`effect_info_list`)),
  `video_duration` bigint(20) DEFAULT NULL,
  `sticker_info_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`sticker_info_list`)),
  `video_mention_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`video_mention_list`)),
  `is_stem_verified` tinyint(1) DEFAULT NULL,
  `type` text DEFAULT NULL,
  `video_label` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`video_label`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `comments`
--
ALTER TABLE `comments`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `follower`
--
ALTER TABLE `follower`
  ADD PRIMARY KEY (`username`,`request_username`),
  ADD UNIQUE KEY `username_2` (`username`,`request_username`),
  ADD KEY `request_username_idx` (`request_username`);

--
-- Indizes für die Tabelle `following`
--
ALTER TABLE `following`
  ADD PRIMARY KEY (`username`,`request_username`),
  ADD KEY `idx_request_username` (`request_username`);

--
-- Indizes für die Tabelle `playlist`
--
ALTER TABLE `playlist`
  ADD PRIMARY KEY (`playlist_id`);

--
-- Indizes für die Tabelle `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`username`),
  ADD UNIQUE KEY `Username_UNIQUE` (`username`),
  ADD KEY `fk_User_videos1_idx` (`videos_id`),
  ADD KEY `fk_User_Playlist1_idx` (`playlist_playlist_id`);

--
-- Indizes für die Tabelle `videos`
--
ALTER TABLE `videos`
  ADD PRIMARY KEY (`id`);

--
-- Constraints der exportierten Tabellen
--

--
-- Constraints der Tabelle `follower`
--
ALTER TABLE `follower`
  ADD CONSTRAINT `request_username` FOREIGN KEY (`request_username`) REFERENCES `user` (`username`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Constraints der Tabelle `following`
--
ALTER TABLE `following`
  ADD CONSTRAINT `fk_following_user` FOREIGN KEY (`request_username`) REFERENCES `user` (`username`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints der Tabelle `user`
--
ALTER TABLE `user`
  ADD CONSTRAINT `fk_User_Playlist1` FOREIGN KEY (`playlist_playlist_id`) REFERENCES `playlist` (`playlist_id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
