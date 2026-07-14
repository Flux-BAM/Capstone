-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 28, 2026 at 02:34 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `brewinsight`
--

-- --------------------------------------------------------

--
-- Table structure for table `ingredients`
--

CREATE TABLE `ingredients` (
  `id` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `stock` float DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ingredients`
--

INSERT INTO `ingredients` (`id`, `name`, `stock`, `unit`) VALUES
(1, 'Arla Fresh Milk', 574, 'ml'),
(2, 'Selecta 3.8L Ice Cream', 1010, 'g'),
(3, 'Nescafé Classic', 888, 'g'),
(4, 'Caramel Macchiato Powder', 1000, 'g'),
(5, 'Milk Chocolate Powder', 1000, 'g'),
(6, 'Cappuccino Powder', 1000, 'g'),
(7, 'Dalgona Powder', 1000, 'g'),
(8, 'Blueberry Fruit Syrup', 1010, 'ml'),
(9, 'Strawberry Fruit Syrup', 1000, 'ml'),
(10, 'Green Apple Fruit Syrup', 1000, 'ml'),
(11, 'Chocolate Syrup', 1000, 'ml'),
(12, 'Cookies and Cream Milktea Powder', 944, 'g'),
(13, 'Chocolate Milktea Powder', 1000, 'g'),
(14, 'Taro Milktea Powder', 1000, 'g'),
(15, 'Wintermelon Milktea Powder', 1000, 'g'),
(16, 'Okinawa Milktea Powder', 2000, 'g'),
(17, 'Matcha Milktea Powder', 1972, 'g'),
(18, 'Cucumber Lemonade Powder', 2000, 'g'),
(19, 'Blue Lemonade Powder', 2000, 'g'),
(20, 'Lemon Iced Tea Powder', 2000, 'g'),
(21, 'Red Iced Tea Powder', 2000, 'g'),
(22, '16oz Cup & Lid', 100, 'pcs'),
(23, 'Fries Cup', 997, 'pcs'),
(27, 'Ham', 3000, 'pcs'),
(28, 'Cheese', 3000, 'pcs'),
(29, 'Waffle Powder', 3000, 'g'),
(31, 'Condensed Milk', 1242, 'g'),
(32, 'White Chocolate Syrup', 1000, 'ml'),
(33, 'Caramel Syrup', 1000, 'ml'),
(34, 'Sweetener', 8995, 'ml'),
(35, 'Mocha Powder', 5000, 'g'),
(36, 'French Vanilla Powder', 5000, 'g'),
(37, 'Cookies', 100, 'pcs'),
(38, 'Siomai', 94, 'pcs'),
(39, 'Kikiam', 47, 'pcs'),
(40, 'Lumpia', 50, 'pcs'),
(41, 'Fries', 400, 'g'),
(42, 'Tuna Flakes', 100, 'g'),
(43, 'Bread', 5000, 'pcs'),
(45, 'Hotdog', 29, 'pcs');

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `category` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `price`, `stock`, `category`) VALUES
(1, 'Americano', 50.00, 53, 'icedcoffee'),
(2, 'Mocha', 55.00, 44, 'icedcoffee'),
(3, 'Dirty Matcha', 55.00, 43, 'icedcoffee'),
(4, 'Caffe Latte', 55.00, 32, 'icedcoffee'),
(5, 'Cappuccino', 55.00, 50, 'icedcoffee'),
(6, 'Dalgona', 55.00, 50, 'icedcoffee'),
(7, 'Caramel Macchiato', 55.00, 50, 'icedcoffee'),
(8, 'Blueberry Latte', 55.00, 48, 'icedlatte'),
(9, 'Strawberry Latte', 55.00, 50, 'icedlatte'),
(10, 'Green apple Latte', 55.00, 50, 'icedlatte'),
(11, 'Choco Latte', 55.00, 50, 'icedlatte'),
(12, 'Cookies and Cream', 55.00, 47, 'milktea'),
(13, 'Chocolate', 55.00, 50, 'milktea'),
(14, 'Matcha', 55.00, 46, 'milktea'),
(15, 'Taro', 55.00, 49, 'milktea'),
(16, 'Wintermelon', 55.00, 50, 'milktea'),
(17, 'Okinawa', 55.00, 50, 'milktea'),
(18, 'Coffee Float', 65.00, 50, 'creamyfloats'),
(19, 'Chocolate Float', 65.00, 50, 'creamyfloats'),
(20, 'Blueberry Float', 55.00, 50, 'summerfloats'),
(21, 'Vanilla Coke Float', 55.00, 50, 'summerfloats'),
(22, 'Strawberry Float', 55.00, 50, 'summerfloats'),
(23, 'Green Apple Float', 55.00, 50, 'summerfloats'),
(24, 'Cucumber Lemonade', 40.00, 50, 'lemonadetea'),
(25, 'Blue Lemonade', 40.00, 50, 'lemonadetea'),
(26, 'Lemon Iced Tea', 40.00, 50, 'lemonadetea'),
(27, 'Red Iced Tea', 40.00, 50, 'lemonadetea'),
(28, 'Matcha Latte', 55.00, 50, 'matchaseries'),
(29, 'Matcha Berry', 55.00, 50, 'matchaseries'),
(30, 'Blueberry Matcha', 55.00, 50, 'matchaseries'),
(31, 'Matcha Caramel', 55.00, 50, 'matchaseries'),
(32, 'White Chocolate Matcha', 55.00, 50, 'matchaseries'),
(33, 'Americano Hot', 30.00, 48, 'hotcoffee'),
(34, 'Caffe Latte Hot\r\n', 35.00, 50, 'hotcoffee'),
(35, 'Cappuccino Hot', 40.00, 50, 'hotcoffee'),
(36, 'Mocha Hot', 40.00, 50, 'hotcoffee'),
(37, 'Caramel Macchiato Hot', 40.00, 50, 'hotcoffee'),
(38, 'French Vanilla Latte Hot', 50.00, 50, 'hotcoffee'),
(39, 'Tuna Sandwich', 40.00, 48, 'snacks'),
(40, 'Ham and Cheese Sandwich', 40.00, 50, 'snacks'),
(41, 'Waffle', 35.00, 42, 'snacks'),
(42, 'Cookies', 25.00, -39, 'snacks'),
(43, 'Siomai', 30.00, 29, 'snacks'),
(44, 'Kikiam', 30.00, 48, 'snacks'),
(45, 'Lumpia', 30.00, 46, 'snacks'),
(46, 'Fries', 30.00, 24, 'snacks');

-- --------------------------------------------------------

--
-- Table structure for table `recipes`
--

CREATE TABLE `recipes` (
  `id` int(11) NOT NULL,
  `product_id` int(11) DEFAULT NULL,
  `ingredient_id` int(11) DEFAULT NULL,
  `quantity` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `recipes`
--

INSERT INTO `recipes` (`id`, `product_id`, `ingredient_id`, `quantity`) VALUES
(1, 20, 8, 30),
(2, 21, 11, 30),
(3, 22, 9, 30),
(4, 23, 10, 30),
(5, 20, 2, 60),
(6, 21, 2, 60),
(7, 22, 2, 60),
(8, 22, 2, 60),
(9, 28, 17, 15),
(10, 29, 17, 15),
(11, 30, 17, 15),
(12, 31, 17, 15),
(13, 32, 17, 15),
(14, 28, 31, 40),
(15, 29, 31, 40),
(16, 30, 31, 40),
(17, 31, 31, 40),
(18, 32, 31, 40),
(19, 28, 32, 15),
(20, 29, 9, 29),
(21, 30, 8, 29),
(22, 31, 33, 29),
(23, 32, 32, 15),
(24, 28, 1, 115),
(25, 29, 1, 115),
(26, 30, 1, 115),
(27, 31, 1, 115),
(28, 32, 1, 115),
(29, 12, 12, 28),
(30, 13, 13, 28),
(31, 14, 17, 28),
(32, 15, 14, 28),
(33, 16, 15, 28),
(34, 17, 16, 28),
(35, 12, 34, 2),
(36, 13, 34, 2),
(37, 14, 34, 2),
(38, 15, 34, 2),
(39, 16, 34, 2),
(40, 17, 34, 2),
(41, 8, 31, 29),
(42, 9, 9, 29),
(43, 10, 31, 29),
(44, 1, 31, 29),
(45, 8, 8, 29),
(46, 9, 9, 29),
(47, 10, 10, 29),
(48, 11, 11, 29),
(49, 8, 1, 118),
(50, 9, 1, 118),
(51, 10, 1, 118),
(52, 11, 1, 118),
(53, 1, 3, 28),
(54, 2, 3, 28),
(55, 3, 3, 28),
(56, 4, 3, 28),
(57, 5, 3, 28),
(58, 6, 3, 28),
(59, 7, 3, 28),
(60, 1, 1, 118),
(61, 2, 1, 118),
(62, 3, 1, 118),
(63, 4, 1, 118),
(64, 5, 1, 118),
(65, 6, 1, 118),
(66, 7, 1, 118),
(67, 24, 18, 15),
(68, 25, 19, 15),
(69, 26, 20, 15),
(70, 27, 21, 15),
(71, 24, 34, 2.5),
(72, 25, 34, 2.5),
(73, 26, 34, 2.5),
(74, 27, 34, 2.5),
(75, 18, 3, 10),
(76, 19, 19, 10),
(77, 18, 11, 29),
(78, 19, 11, 29),
(79, 18, 1, 118),
(80, 19, 1, 118),
(81, 18, 2, 70),
(82, 19, 2, 70),
(83, 33, 3, 10),
(84, 34, 3, 10),
(85, 35, 3, 10),
(86, 36, 3, 10),
(87, 37, 3, 10),
(88, 38, 3, 10),
(89, 35, 6, 28),
(90, 36, 35, 28),
(91, 37, 4, 28),
(92, 38, 36, 28),
(93, 35, 1, 118),
(94, 36, 1, 118),
(95, 37, 1, 118),
(96, 38, 1, 118),
(97, 2, 35, 15),
(98, 3, 17, 15),
(99, 5, 6, 15),
(100, 6, 7, 15),
(101, 7, 4, 15),
(102, 11, 31, 29),
(103, 1, 22, 1),
(104, 2, 22, 1),
(105, 3, 22, 1),
(106, 4, 22, 1),
(107, 5, 22, 1),
(108, 6, 22, 1),
(109, 7, 22, 1),
(110, 8, 22, 1),
(111, 9, 22, 1),
(112, 10, 22, 1),
(113, 11, 22, 1),
(114, 12, 22, 1),
(115, 13, 22, 1),
(116, 14, 22, 1),
(117, 15, 22, 1),
(118, 16, 22, 1),
(119, 17, 22, 1),
(120, 18, 22, 1),
(121, 19, 22, 1),
(122, 20, 22, 1),
(123, 21, 22, 1),
(124, 22, 22, 1),
(125, 23, 22, 1),
(126, 24, 22, 1),
(127, 25, 22, 1),
(128, 26, 22, 1),
(129, 27, 22, 1),
(130, 28, 22, 1),
(131, 29, 22, 1),
(132, 30, 22, 1),
(133, 31, 22, 1),
(134, 32, 22, 1),
(135, 33, 22, 1),
(136, 34, 22, 1),
(137, 35, 22, 1),
(138, 36, 22, 1),
(139, 37, 22, 1),
(140, 38, 22, 1),
(141, 43, 38, 3),
(142, 44, 39, 3),
(143, 45, 40, 3),
(144, 41, 29, 50),
(145, 39, 42, 20),
(146, 39, 43, 2),
(147, 40, 27, 1),
(148, 40, 28, 1),
(149, 40, 43, 2),
(150, 46, 41, 100),
(151, 46, 23, 1);

-- --------------------------------------------------------

--
-- Table structure for table `sales`
--

CREATE TABLE `sales` (
  `id` int(11) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `customer_name` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sales`
--

INSERT INTO `sales` (`id`, `total`, `created_at`, `customer_name`) VALUES
(1, 50.00, '2026-03-07 22:22:37', NULL),
(2, 55.00, '2026-03-07 22:23:03', NULL),
(3, 55.00, '2026-03-07 22:55:52', NULL),
(4, 55.00, '2026-03-07 23:00:45', NULL),
(5, 55.00, '2026-03-07 23:00:50', NULL),
(6, 50.00, '2026-03-07 23:01:05', NULL),
(7, 50.00, '2026-03-07 23:32:54', NULL),
(8, 55.00, '2026-03-07 23:33:07', NULL),
(9, 55.00, '2026-03-07 23:33:38', NULL),
(10, 50.00, '2026-03-07 23:38:13', NULL),
(11, 50.00, '2026-03-07 23:43:55', NULL),
(12, 50.00, '2026-03-07 23:44:01', NULL),
(13, 30.00, '2026-03-08 00:19:44', NULL),
(14, 50.00, '2026-03-08 00:25:48', NULL),
(15, 30.00, '2026-03-08 00:26:15', NULL),
(16, 55.00, '2026-03-08 10:45:41', 's'),
(17, 50.00, '2026-03-08 11:15:05', 'john'),
(18, 110.00, '2026-03-12 13:03:03', 'evelyn'),
(19, 50.00, '2026-03-12 14:23:06', 'evelyn'),
(20, 55.00, '2026-03-12 14:32:47', 'a'),
(21, 55.00, '2026-03-12 18:30:19', 'johns'),
(22, 110.00, '2026-03-17 15:21:31', 'fel'),
(23, 55.00, '2026-03-17 15:49:14', '2'),
(24, 55.00, '2026-03-17 16:06:48', '5'),
(25, 55.00, '2026-03-17 16:12:20', '3'),
(26, 55.00, '2026-03-17 17:18:18', 'wef'),
(27, 110.00, '2026-03-17 21:48:42', 'jan jan'),
(28, 55.00, '2026-03-23 19:04:26', '123'),
(29, 110.00, '2026-03-24 14:41:14', 'za'),
(30, 55.00, '2026-03-26 08:56:05', 'pjohn'),
(31, 100.00, '2026-03-26 15:47:42', 'jogn'),
(32, 110.00, '2026-03-26 15:56:38', 'fvd'),
(33, 55.00, '2026-03-26 15:57:11', 'v'),
(34, 55.00, '2026-03-26 16:37:47', '123'),
(35, 275.00, '2026-03-26 16:41:26', '2'),
(36, 50.00, '2026-03-26 16:45:39', 'eve'),
(37, 110.00, '2026-03-26 17:14:58', '321'),
(38, 55.00, '2026-03-26 17:37:53', 'john'),
(39, 55.00, '2026-03-26 17:42:35', '53'),
(40, 55.00, '2026-03-26 17:50:40', '123'),
(41, 105.00, '2026-03-26 18:46:24', 'lynlyn'),
(42, 115.00, '2026-03-26 19:09:58', 'eve'),
(43, 55.00, '2026-03-26 21:02:37', 'fel'),
(44, 50.00, '2026-03-27 00:01:43', '22'),
(45, 50.00, '2026-03-27 00:09:35', '23'),
(46, 55.00, '2026-03-27 00:20:35', '26'),
(47, 105.00, '2026-03-27 00:21:25', '28'),
(48, 30.00, '2026-03-27 01:44:11', 'feljans'),
(49, 330.00, '2026-03-27 01:56:29', 'feljan'),
(50, 210.00, '2026-03-27 01:57:26', 'evelyn'),
(51, 30.00, '2026-03-27 12:40:23', 'john'),
(52, 60.00, '2026-03-27 12:43:15', 'evelynn'),
(53, 30.00, '2026-03-27 14:04:21', 'eve'),
(54, 30.00, '2026-03-27 14:10:07', '0909'),
(55, 40.00, '2026-03-27 15:57:05', 'eve'),
(56, 40.00, '2026-03-27 15:57:46', '2133'),
(57, 25.00, '2026-03-27 16:26:34', 'eve'),
(58, 250.00, '2026-03-27 16:47:34', 'e'),
(59, 90.00, '2026-03-27 16:51:04', 'janjan'),
(60, 30.00, '2026-03-27 16:52:42', 'eve'),
(61, 35.00, '2026-03-27 16:53:07', 'evelyn'),
(62, 360.00, '2026-03-27 17:40:02', 'evelyn'),
(63, 105.00, '2026-03-27 17:47:20', 'xzsc'),
(64, 25.00, '2026-03-27 17:48:17', '56'),
(65, 30.00, '2026-03-27 17:56:02', 'fel'),
(66, 35.00, '2026-03-27 18:34:28', 'eve'),
(67, 25.00, '2026-03-29 18:01:22', 'jan'),
(68, 25.00, '2026-03-29 18:25:36', 'eve'),
(69, 200.00, '2026-03-29 19:01:52', '1'),
(70, 50.00, '2026-03-29 20:26:18', '123'),
(71, 25.00, '2026-03-29 20:29:06', 'eve'),
(72, 25.00, '2026-03-29 20:35:52', '432'),
(73, 25.00, '2026-03-29 20:37:11', '432'),
(74, 25.00, '2026-03-29 20:38:13', '123'),
(75, 25.00, '2026-03-29 20:44:40', '3213'),
(76, 25.00, '2026-03-29 20:46:16', '3121'),
(77, 25.00, '2026-03-29 20:53:14', '4321'),
(78, 25.00, '2026-03-29 20:55:31', '54'),
(79, 25.00, '2026-03-29 20:57:19', '231'),
(80, 50.00, '2026-03-29 21:05:15', '300'),
(81, 30.00, '2026-03-29 21:26:45', 'fel'),
(82, 25.00, '2026-03-29 23:08:57', 'fel'),
(83, 25.00, '2026-03-30 08:03:45', 'fel'),
(84, 55.00, '2026-03-30 08:12:39', 'eve'),
(85, 60.00, '2026-03-30 08:22:10', 'eve'),
(86, 85.00, '2026-03-30 08:36:41', 'feljan'),
(87, 25.00, '2026-03-30 08:42:47', 'fel'),
(88, 55.00, '2026-03-30 09:10:52', 'eve'),
(89, 55.00, '2026-03-30 09:10:53', 'eve'),
(90, 30.00, '2026-03-30 09:24:05', 'feljan1'),
(91, 500.00, '2026-03-30 09:25:21', 'feljan1'),
(92, 125.00, '2026-03-30 09:46:30', 's'),
(93, 25.00, '2026-03-30 09:54:25', '2'),
(94, 25.00, '2026-03-30 10:19:45', '3 '),
(95, 30.00, '2026-04-09 13:42:58', '123'),
(96, 25.00, '2026-04-09 15:22:24', '321'),
(97, 25.00, '2026-04-09 15:39:06', '456'),
(98, 25.00, '2026-04-09 15:49:29', 'feljan23'),
(99, 25.00, '2026-04-09 15:49:54', '21333'),
(100, 25.00, '2026-04-09 16:39:24', '444'),
(101, 110.00, '2026-04-09 17:16:46', 'eve'),
(102, 50.00, '2026-04-09 17:22:36', 'felj'),
(103, 50.00, '2026-04-09 17:26:04', 'fel'),
(104, 105.00, '2026-04-09 19:16:55', 'feljan'),
(105, 50.00, '2026-04-27 12:02:34', 'asd'),
(106, 60.00, '2026-04-27 12:31:19', 'dsa'),
(107, 100.00, '2026-04-27 12:56:42', 'qwe'),
(108, 25.00, '2026-04-27 13:33:29', 'po'),
(109, 25.00, '2026-04-27 18:46:55', 'ee'),
(110, 50.00, '2026-04-28 19:09:15', 'ha'),
(111, 25.00, '2026-04-28 19:11:55', 'ah'),
(112, 25.00, '2026-04-28 19:45:53', 'fel'),
(113, 50.00, '2026-04-28 19:51:11', '123'),
(114, 25.00, '2026-04-28 20:05:35', '321'),
(115, 25.00, '2026-04-28 20:06:55', '12345'),
(116, 25.00, '2026-04-28 20:18:53', '20');

-- --------------------------------------------------------

--
-- Table structure for table `sale_items`
--

CREATE TABLE `sale_items` (
  `id` int(11) NOT NULL,
  `sale_id` int(11) DEFAULT NULL,
  `product_id` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sale_items`
--

INSERT INTO `sale_items` (`id`, `sale_id`, `product_id`, `quantity`, `price`, `subtotal`) VALUES
(8, 8, 8, 1, 55.00, 55.00),
(9, 9, 8, 1, 55.00, 55.00),
(11, 11, 1, 1, 50.00, 50.00),
(12, 12, 1, 1, 50.00, 50.00),
(13, 13, 33, 1, 30.00, 30.00),
(16, 16, 5, 1, 55.00, 55.00),
(17, 17, 1, 1, 50.00, 50.00),
(19, 19, 1, 1, 50.00, 50.00),
(39, 35, 4, 1, 55.00, 55.00),
(41, 35, 4, 1, 55.00, 55.00),
(42, 35, 4, 1, 55.00, 55.00),
(43, 35, 4, 1, 55.00, 55.00),
(44, 36, 1, 1, 50.00, 50.00),
(46, 38, 2, 1, 55.00, 55.00),
(47, 39, 4, 1, 55.00, 55.00),
(93, 80, 42, 1, 25.00, 25.00),
(94, 80, 42, 1, 25.00, 25.00),
(95, 81, 43, 1, 30.00, 30.00),
(96, 82, 42, 1, 25.00, 25.00),
(97, 83, 42, 1, 25.00, 25.00),
(98, 84, 12, 1, 55.00, 55.00),
(99, 85, 43, 2, 30.00, 60.00),
(100, 86, 14, 1, 55.00, 55.00),
(101, 86, 43, 1, 30.00, 30.00),
(102, 87, 42, 1, 25.00, 25.00),
(103, 88, 4, 1, 55.00, 55.00),
(104, 89, 4, 1, 55.00, 55.00),
(105, 90, 46, 1, 30.00, 30.00),
(106, 91, 42, 20, 25.00, 500.00),
(107, 92, 42, 5, 25.00, 125.00),
(108, 93, 42, 1, 25.00, 25.00),
(109, 94, 42, 1, 25.00, 25.00),
(110, 95, 46, 1, 30.00, 30.00),
(111, 96, 42, 1, 25.00, 25.00),
(112, 97, 42, 1, 25.00, 25.00),
(113, 98, 42, 1, 25.00, 25.00),
(114, 99, 42, 1, 25.00, 25.00),
(115, 100, 42, 1, 25.00, 25.00),
(116, 101, 12, 2, 55.00, 110.00),
(117, 102, 42, 2, 25.00, 50.00),
(118, 103, 42, 2, 25.00, 50.00),
(119, 104, 42, 3, 25.00, 75.00),
(120, 104, 46, 1, 30.00, 30.00),
(121, 105, 42, 2, 25.00, 50.00),
(122, 106, 43, 2, 30.00, 60.00),
(123, 107, 1, 2, 50.00, 100.00),
(124, 108, 42, 1, 25.00, 25.00),
(125, 109, 42, 1, 25.00, 25.00),
(126, 110, 42, 2, 25.00, 50.00),
(127, 111, 42, 1, 25.00, 25.00),
(129, 113, 42, 2, 25.00, 50.00),
(130, 114, 42, 1, 25.00, 25.00),
(131, 115, 42, 1, 25.00, 25.00);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`) VALUES
(1, 'feljan', 'scrypt:32768:8:1$RZ3oQVJpAvXh1xa2$7341d79963247762e316548c6abc04c97570aff99382d90211504dc165d0786b239c2575cc458d6dd93f8d54efdd9d0c6b4451c1703ec5e2b7fbbe1bbc75bda1'),
(2, 'jan', 'scrypt:32768:8:1$ZYH7OBRkQLFRPad9$e6a29aadb74fed3361bcfcfa625c19671a9acd2441c5ff9e69b1d753829c3aa5f38beb92d85dfbf8f4800e95b757ba6be7d858170516a27553bbe6d0ebc07fd9'),
(3, 'fel', 'scrypt:32768:8:1$AgDZTWDkqn7xqT5z$2ae9c5a265b49d8dfa6d9bf573aef04d2a67f0a8dbd545d60d23b49359a8e2ebe1cf36fd0c27b863ced7d4eddecf98a55bfbea16a454773640168caa04006f7c'),
(4, 'evelyn', 'scrypt:32768:8:1$HvnH4tfF5TxCkScX$8a978def4e2cd61e85575d39888ca2b33918c87c00336007a75aa43b8aa2d2bb44b764b08b36a232b933df9a443a01883d0c3d8acbd2063e885edd439243e61a'),
(5, 'evelyn123', 'scrypt:32768:8:1$MWS3gc5RJCUfIGVK$fa2f5b3ba714d8c3f3c144395eb0a23264ac103ba3d45e517efd8b640dd283a37e0fe2588f7018276c4d1ac3cc675a2b321e6e6b37ae7cbee660921fbba8cd36'),
(6, 'eve123', 'scrypt:32768:8:1$UrlOL6XRD9YyBpSy$b64a193d0c3d91fe5f1330046dcd30b50fb10ceb8e56f05aa8102120a7da1369f438d5d1f4e39688ef8165cc4a550e5f150ad2f3377a30ff5b4fed846793bc63');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ingredients`
--
ALTER TABLE `ingredients`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `products`
--
ALTER TABLE `products`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `recipes`
--
ALTER TABLE `recipes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `product_id` (`product_id`),
  ADD KEY `ingredient_id` (`ingredient_id`);

--
-- Indexes for table `sales`
--
ALTER TABLE `sales`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sale_items`
--
ALTER TABLE `sale_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sale_id` (`sale_id`),
  ADD KEY `product_id` (`product_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ingredients`
--
ALTER TABLE `ingredients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `products`
--
ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=95;

--
-- AUTO_INCREMENT for table `recipes`
--
ALTER TABLE `recipes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=154;

--
-- AUTO_INCREMENT for table `sales`
--
ALTER TABLE `sales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=117;

--
-- AUTO_INCREMENT for table `sale_items`
--
ALTER TABLE `sale_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=133;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `recipes`
--
ALTER TABLE `recipes`
  ADD CONSTRAINT `recipes_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  ADD CONSTRAINT `recipes_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredients` (`id`);

--
-- Constraints for table `sale_items`
--
ALTER TABLE `sale_items`
  ADD CONSTRAINT `sale_items_ibfk_1` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`),
  ADD CONSTRAINT `sale_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
