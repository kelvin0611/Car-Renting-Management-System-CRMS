-- Create database
CREATE DATABASE p2p_car_rental;

-- Use database
USE p2p_car_rental;

-- User table (stores all user information including owners and renters)
CREATE TABLE `User` (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    userType VARCHAR(20),
    name VARCHAR(100),
    gmail VARCHAR(100),
    identityNo VARCHAR(50),
    address VARCHAR(255),
    password VARCHAR(128),
    userStatus VARCHAR(20) NOT NULL DEFAULT 'active',
    createTime DATETIME,
    updateTime DATETIME
);

-- Owner table (stores owner-specific information)
CREATE TABLE Owner (
    owner_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    rating DECIMAL(2,1),
    verificationStatus VARCHAR(20) NOT NULL DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

-- Renter table (stores renter-specific information)
CREATE TABLE Renter (
    renter_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    rating DECIMAL(2,1),
    balance DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

-- Vehicle table (stores vehicle information listed for rental)
-- owner_id references Owner(owner_id) (NOT User.user_id)
CREATE TABLE Vehicle (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id INT,
    carType VARCHAR(50),
    lisenceNum VARCHAR(50),
    year INT,
    seatNum INT,
    status VARCHAR(20),
    photoURL VARCHAR(255),
    registerTime DATETIME,
    dailyPrice DECIMAL(10,2),
    brand VARCHAR(50),
    model VARCHAR(50),
    location VARCHAR(100),
    description TEXT,
    verificationStatus VARCHAR(20) NOT NULL DEFAULT 'pending',
    FOREIGN KEY (owner_id) REFERENCES Owner(owner_id)
);

-- Insurance table (stores available insurance plans)
CREATE TABLE Insurance (
    insurance_id INT PRIMARY KEY AUTO_INCREMENT,
    types VARCHAR(50),
    fee DECIMAL(10,2),
    validityPeriod VARCHAR(50),
    company VARCHAR(100),
    description TEXT
);

-- Rental table (stores rental transaction records)
CREATE TABLE Rental (
    rental_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id INT,
    renter_id INT,
    rentalStartTime DATETIME,
    rentalEndTime DATETIME,
    pickupLocation VARCHAR(255),
    dropoffLocation VARCHAR(255),
    totalAmount DECIMAL(10,2),
    orderStatus VARCHAR(20),
    paymentStatus VARCHAR(20),
    returnTime DATETIME,
    dailyPrice DECIMAL(10,2),
    createTime DATETIME,
    insurance_id INT,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id),
    FOREIGN KEY (renter_id) REFERENCES Renter(renter_id),
    FOREIGN KEY (insurance_id) REFERENCES Insurance(insurance_id)
);

-- RentalInsurance table (junction table for rental-insurance many-to-many relationship)
CREATE TABLE RentalInsurance (
    rental_id INT,
    insurance_id INT,
    PolicyNumer VARCHAR(100),
    effectiveDate DATE,
    PRIMARY KEY (rental_id, insurance_id),
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id),
    FOREIGN KEY (insurance_id) REFERENCES Insurance(insurance_id)
);

-- Payment table (stores payment transaction records)
CREATE TABLE Payment (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    rental_id INT,
    paymentAmount DECIMAL(10,2),
    paymentMethod VARCHAR(50),
    paymentTime DATETIME,
    TransactionNumber VARCHAR(100),
    paymentStatus VARCHAR(20),
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id)
);

-- Helpful indexes (performance / admin dashboard queries)
CREATE INDEX idx_user_gmail ON `User`(gmail);
CREATE INDEX idx_vehicle_status ON Vehicle(status);
CREATE INDEX idx_vehicle_carType ON Vehicle(carType);
CREATE INDEX idx_rental_vehicle_id ON Rental(vehicle_id);
CREATE INDEX idx_rental_renter_id ON Rental(renter_id);
CREATE INDEX idx_rental_orderStatus ON Rental(orderStatus);
CREATE INDEX idx_rental_paymentStatus ON Rental(paymentStatus);
CREATE INDEX idx_payment_rental_id ON Payment(rental_id);