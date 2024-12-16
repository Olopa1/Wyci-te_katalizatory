CREATE TABLE IF NOT EXISTS `Cars` (
	`car_id` int AUTO_INCREMENT NOT NULL UNIQUE,
	`register_plate` varchar(255) NOT NULL,
	`last_x_position` int NOT NULL,
	`last_y_position` int NOT NULL,
	`is_on_parking` boolean NOT NULL,
	PRIMARY KEY (`car_id`)
);

CREATE TABLE IF NOT EXISTS `Reserved_spots` (
	`spot_id` int NOT NULL UNIQUE,
	`car_id` int NOT NULL
);


ALTER TABLE `Reserved_spots` ADD CONSTRAINT `Reserved_spots_fk1` FOREIGN KEY (`car_id`) REFERENCES `Cars`(`car_id`);