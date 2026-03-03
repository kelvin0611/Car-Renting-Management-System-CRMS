-- Migration 001: add userStatus & verificationStatus columns (non-destructive)
-- Run this ONLY if you already created tables before, and you do NOT want to reset DB.

USE p2p_car_rental;

ALTER TABLE `User`
  ADD COLUMN userStatus VARCHAR(20) NOT NULL DEFAULT 'active',
  ADD COLUMN createTime DATETIME NULL,
  ADD COLUMN updateTime DATETIME NULL;

ALTER TABLE Owner
  ADD COLUMN verificationStatus VARCHAR(20) NOT NULL DEFAULT 'pending';

ALTER TABLE Vehicle
  ADD COLUMN verificationStatus VARCHAR(20) NOT NULL DEFAULT 'pending';

ALTER TABLE Rental
  ADD COLUMN pickupLocation VARCHAR(255) NULL,
  ADD COLUMN dropoffLocation VARCHAR(255) NULL;

CREATE INDEX idx_user_gmail ON `User`(gmail);
CREATE INDEX idx_vehicle_status ON Vehicle(status);
CREATE INDEX idx_vehicle_carType ON Vehicle(carType);
CREATE INDEX idx_rental_vehicle_id ON Rental(vehicle_id);
CREATE INDEX idx_rental_renter_id ON Rental(renter_id);
CREATE INDEX idx_rental_orderStatus ON Rental(orderStatus);
CREATE INDEX idx_rental_paymentStatus ON Rental(paymentStatus);
CREATE INDEX idx_payment_rental_id ON Payment(rental_id);

