-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 27, 2026 at 04:39 PM
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
  `unit` varchar(20) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ingredients`
--

INSERT INTO `ingredients` (`id`, `name`, `stock`, `unit`, `created_at`) VALUES
(1, 'Arla Fresh Milk', 1882, 'ml', '2026-05-25 13:44:15'),
(2, 'Selecta 3.8L Ice Cream', 1010, 'g', '2026-05-25 13:44:15'),
(3, 'Nescafé Classic', 850, 'g', '2026-05-25 13:44:15'),
(4, 'Caramel Macchiato Powder', 1000, 'g', '2026-05-25 13:44:15'),
(5, 'Milk Chocolate Powder', 1000, 'g', '2026-05-25 13:44:15'),
(6, 'Cappuccino Powder', 1000, 'g', '2026-05-25 13:44:15'),
(7, 'Dalgona Powder', 1000, 'g', '2026-05-25 13:44:15'),
(8, 'Blueberry Fruit Syrup', 1010, 'ml', '2026-05-25 13:44:15'),
(9, 'Strawberry Fruit Syrup', 1000, 'ml', '2026-05-25 13:44:15'),
(10, 'Green Apple Fruit Syrup', 1000, 'ml', '2026-05-25 13:44:15'),
(11, 'Chocolate Syrup', 1000, 'ml', '2026-05-25 13:44:15'),
(12, 'Cookies and Cream Milktea Powder', 944, 'g', '2026-05-25 13:44:15'),
(13, 'Chocolate Milktea Powder', 1000, 'g', '2026-05-25 13:44:15'),
(14, 'Taro Milktea Powder', 972, 'g', '2026-05-25 13:44:15'),
(15, 'Wintermelon Milktea Powder', 1000, 'g', '2026-05-25 13:44:15'),
(16, 'Okinawa Milktea Powder', 2000, 'g', '2026-05-25 13:44:15'),
(17, 'Matcha Milktea Powder', 1972, 'g', '2026-05-25 13:44:15'),
(18, 'Cucumber Lemonade Powder', 2000, 'g', '2026-05-25 13:44:15'),
(19, 'Blue Lemonade Powder', 2000, 'g', '2026-05-25 13:44:15'),
(20, 'Lemon Iced Tea Powder', 2000, 'g', '2026-05-25 13:44:15'),
(21, 'Red Iced Tea Powder', 2000, 'g', '2026-05-25 13:44:15'),
(22, '16oz Cup & Lid', 100, 'pcs', '2026-05-25 13:44:15'),
(23, 'Fries Cup', 997, 'pcs', '2026-05-25 13:44:15'),
(27, 'Ham', 3000, 'pcs', '2026-05-25 13:44:15'),
(28, 'Cheese', 3000, 'pcs', '2026-05-25 13:44:15'),
(29, 'Waffle Powder', 3000, 'g', '2026-05-25 13:44:15'),
(31, 'Condensed Milk', 1213, 'g', '2026-05-25 13:44:15'),
(32, 'White Chocolate Syrup', 1000, 'ml', '2026-05-25 13:44:15'),
(33, 'Caramel Syrup', 1000, 'ml', '2026-05-25 13:44:15'),
(34, 'Sweetener', 8993, 'ml', '2026-05-25 13:44:15'),
(35, 'Mocha Powder', 5000, 'g', '2026-05-25 13:44:15'),
(36, 'French Vanilla Powder', 5000, 'g', '2026-05-25 13:44:15'),
(37, 'Cookies', 94, 'pcs', '2026-05-25 13:44:15'),
(38, 'Siomai', 82, 'pcs', '2026-05-25 13:44:15'),
(39, 'Kikiam', 47, 'pcs', '2026-05-25 13:44:15'),
(40, 'Lumpia', 44, 'pcs', '2026-05-25 13:44:15'),
(41, 'Fries', 1000, 'g', '2026-05-25 13:44:15'),
(42, 'Tuna Flakes', 1000, 'g', '2026-05-25 13:44:15'),
(43, 'Bread', 5000, 'pcs', '2026-05-25 13:44:15'),
(45, 'Hotdog', 29, 'pcs', '2026-05-25 13:44:15');

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `category` varchar(50) DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `price`, `stock`, `category`, `image`) VALUES
(1, 'Americano', 50.00, 52, 'icedcoffee', NULL),
(2, 'Mocha', 55.00, 44, 'icedcoffee', NULL),
(3, 'Dirty Matcha', 55.00, 43, 'icedcoffee', NULL),
(4, 'Caffe Latte', 55.00, 32, 'icedcoffee', NULL),
(5, 'Cappuccino', 55.00, 50, 'icedcoffee', NULL),
(6, 'Dalgona', 55.00, 50, 'icedcoffee', NULL),
(7, 'Caramel Macchiato', 55.00, 50, 'icedcoffee', NULL),
(8, 'Blueberry Latte', 55.00, 48, 'icedlatte', NULL),
(9, 'Strawberry Latte', 55.00, 50, 'icedlatte', NULL),
(10, 'Green apple Latte', 55.00, 50, 'icedlatte', NULL),
(11, 'Choco Latte', 55.00, 50, 'icedlatte', NULL),
(12, 'Cookies and Cream', 55.00, 47, 'milktea', NULL),
(13, 'Chocolate', 55.00, 50, 'milktea', NULL),
(14, 'Matcha', 55.00, 46, 'milktea', NULL),
(15, 'Taro', 55.00, 48, 'milktea', NULL),
(16, 'Wintermelon', 55.00, 50, 'milktea', NULL),
(17, 'Okinawa', 55.00, 50, 'milktea', NULL),
(18, 'Coffee Float', 65.00, 50, 'creamyfloats', NULL),
(19, 'Chocolate Float', 65.00, 50, 'creamyfloats', NULL),
(20, 'Blueberry Float', 55.00, 50, 'summerfloats', NULL),
(21, 'Vanilla Coke Float', 55.00, 50, 'summerfloats', NULL),
(22, 'Strawberry Float', 55.00, 50, 'summerfloats', NULL),
(23, 'Green Apple Float', 55.00, 50, 'summerfloats', NULL),
(24, 'Cucumber Lemonade', 40.00, 50, 'lemonadetea', NULL),
(25, 'Blue Lemonade', 40.00, 50, 'lemonadetea', NULL),
(26, 'Lemon Iced Tea', 40.00, 50, 'lemonadetea', NULL),
(27, 'Red Iced Tea', 40.00, 50, 'lemonadetea', NULL),
(28, 'Matcha Latte', 55.00, 50, 'matchaseries', NULL),
(29, 'Matcha Berry', 55.00, 50, 'matchaseries', NULL),
(30, 'Blueberry Matcha', 55.00, 50, 'matchaseries', NULL),
(31, 'Matcha Caramel', 55.00, 50, 'matchaseries', NULL),
(32, 'White Chocolate Matcha', 55.00, 50, 'matchaseries', NULL),
(33, 'Americano Hot', 30.00, 47, 'hotcoffee', NULL),
(34, 'Caffe Latte Hot\r\n', 35.00, 50, 'hotcoffee', NULL),
(35, 'Cappuccino Hot', 40.00, 50, 'hotcoffee', NULL),
(36, 'Mocha Hot', 40.00, 50, 'hotcoffee', NULL),
(37, 'Caramel Macchiato Hot', 40.00, 50, 'hotcoffee', NULL),
(38, 'French Vanilla Latte Hot', 50.00, 50, 'hotcoffee', NULL),
(39, 'Tuna Sandwich', 40.00, 48, 'snacks', NULL),
(40, 'Ham and Cheese Sandwich', 40.00, 50, 'snacks', NULL),
(41, 'Waffle', 35.00, 42, 'snacks', NULL),
(42, 'Cookies', 25.00, -167, 'snacks', NULL),
(43, 'Siomai', 30.00, 25, 'snacks', NULL),
(44, 'Kikiam', 30.00, 48, 'snacks', NULL),
(45, 'Lumpia', 30.00, 44, 'snacks', NULL),
(46, 'Fries', 30.00, 24, 'snacks', NULL);

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
(151, 46, 23, 1),
(158, 42, 37, 1);

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
  `subtotal` decimal(10,2) DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `created_at`) VALUES
(1, 'feljan', 'scrypt:32768:8:1$RZ3oQVJpAvXh1xa2$7341d79963247762e316548c6abc04c97570aff99382d90211504dc165d0786b239c2575cc458d6dd93f8d54efdd9d0c6b4451c1703ec5e2b7fbbe1bbc75bda1', '2026-05-25 05:48:30'),
(2, 'jan', 'scrypt:32768:8:1$ZYH7OBRkQLFRPad9$e6a29aadb74fed3361bcfcfa625c19671a9acd2441c5ff9e69b1d753829c3aa5f38beb92d85dfbf8f4800e95b757ba6be7d858170516a27553bbe6d0ebc07fd9', '2026-05-25 05:48:30'),
(3, 'fel', 'scrypt:32768:8:1$AgDZTWDkqn7xqT5z$2ae9c5a265b49d8dfa6d9bf573aef04d2a67f0a8dbd545d60d23b49359a8e2ebe1cf36fd0c27b863ced7d4eddecf98a55bfbea16a454773640168caa04006f7c', '2026-05-25 05:48:30'),
(4, 'evelyn', 'scrypt:32768:8:1$HvnH4tfF5TxCkScX$8a978def4e2cd61e85575d39888ca2b33918c87c00336007a75aa43b8aa2d2bb44b764b08b36a232b933df9a443a01883d0c3d8acbd2063e885edd439243e61a', '2026-05-25 05:48:30'),
(5, 'evelyn123', 'scrypt:32768:8:1$MWS3gc5RJCUfIGVK$fa2f5b3ba714d8c3f3c144395eb0a23264ac103ba3d45e517efd8b640dd283a37e0fe2588f7018276c4d1ac3cc675a2b321e6e6b37ae7cbee660921fbba8cd36', '2026-05-25 05:48:30'),
(6, 'eve123', 'scrypt:32768:8:1$UrlOL6XRD9YyBpSy$b64a193d0c3d91fe5f1330046dcd30b50fb10ceb8e56f05aa8102120a7da1369f438d5d1f4e39688ef8165cc4a550e5f150ad2f3377a30ff5b4fed846793bc63', '2026-05-25 05:48:30'),
(7, 'jan1', 'scrypt:32768:8:1$MkMs3yrcDcxlm920$eaa56bafbc60f30f9dcb4f74c78577fd1d9917d6488a931f85c8809184f1f0b4f3360ec88cb598d31e3772616c8bbe2a9bb520ef2dbc0bbb88c7b17bba03fcb6', '2026-07-14 08:39:28');

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=56;

--
-- AUTO_INCREMENT for table `products`
--
ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=103;

--
-- AUTO_INCREMENT for table `recipes`
--
ALTER TABLE `recipes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=166;

--
-- AUTO_INCREMENT for table `sales`
--
ALTER TABLE `sales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=149;

--
-- AUTO_INCREMENT for table `sale_items`
--
ALTER TABLE `sale_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=166;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

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
