-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sty 20, 2025 at 02:32 PM
-- Wersja serwera: 10.4.32-MariaDB
-- Wersja PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `wyciete_katalizatory`
--

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `cars`
--

CREATE TABLE `cars` (
  `car_id` int(11) NOT NULL,
  `register_plate` varchar(255) NOT NULL,
  `last_x_position` int(11) NOT NULL,
  `last_y_position` int(11) NOT NULL,
  `is_on_parking` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `cars`
--

INSERT INTO `cars` (`car_id`, `register_plate`, `last_x_position`, `last_y_position`, `is_on_parking`) VALUES
(1, 'CWL17991', 0, 0, 0),
(2, 'CWL34950', 0, 0, 0),
(3, 'CWL34576', 0, 0, 0),
(4, 'WP5207N', 0, 0, 0),
(5, 'WP14831', 0, 0, 0);

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `reserved_spots`
--

CREATE TABLE `reserved_spots` (
  `spot_id` int(11) NOT NULL,
  `car_id` int(11) NOT NULL,
  `spot_number` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reserved_spots`
--

INSERT INTO `reserved_spots` (`spot_id`, `car_id`, `spot_number`) VALUES
(2, 1, 2),
(3, 2, 4),
(4, 3, 6),
(5, 4, 8);

--
-- Indeksy dla zrzutów tabel
--

--
-- Indeksy dla tabeli `cars`
--
ALTER TABLE `cars`
  ADD PRIMARY KEY (`car_id`),
  ADD UNIQUE KEY `car_id` (`car_id`);

--
-- Indeksy dla tabeli `reserved_spots`
--
ALTER TABLE `reserved_spots`
  ADD UNIQUE KEY `spot_id` (`spot_id`),
  ADD KEY `Reserved_spots_fk1` (`car_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `cars`
--
ALTER TABLE `cars`
  MODIFY `car_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `reserved_spots`
--
ALTER TABLE `reserved_spots`
  MODIFY `spot_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `reserved_spots`
--
ALTER TABLE `reserved_spots`
  ADD CONSTRAINT `Reserved_spots_fk1` FOREIGN KEY (`car_id`) REFERENCES `cars` (`car_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
