CREATE TABLE Users(
    user_id int not null AUTO_INCREMENT UNIQUE;
    first_name varchar(50);
    last_name varchar(50);
    status varchar(50);
    PRIMARY KEY(`user_id`);
);

CREATE TABLE Cars(
    car_id int not null AUTO_INCREMENT UNIQUE;
    register_plate varchar(15);
    last_x_position int;
    last_y_position int;
    reserver_spot int;
    is_on_parking boolean;
    PRIMARY KEY(`car_id`);
);

CREATE TABLE Users_cars(
    user_car_id int not NULL AUTO_INCREMENT UNIQUE;
    car_id int;
    user_id int;
    PRIMARY KEY(`user_car_id`);  
);

ALTER TABLE Users_cars ADD CONSTRAINT FK_Users_cars_car FOREIGN KEY (car_id) REFERENCES Cars(car_id);
ALTER TABLE Users_cars ADD CONSTRAINT FK_Users_cars_user FOREIGN KEY (user_id) REFERENCES Users(user_id);