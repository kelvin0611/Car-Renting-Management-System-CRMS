-- Use p2p_car_rental database
USE p2p_car_rental;

-- Insert User table data (11 records)
-- Users include admin, car owners, and renters with their personal information
INSERT INTO `User` (userType, name, gmail, identityNo, address, password, userStatus, createTime, updateTime) VALUES
('admin', 'admin001', 'admin@gmail.com', 'admin', 'admin', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('renter', 'Alex Wong', 'alexwong@gmail.com', 'B987654321', '456 Kowloon', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('owner', 'Michael Lam', 'michaellam@gmail.com', 'C112233445', '789 Mong Kok', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('owner', 'Sarah Chan', 'sarahchan@gmail.com', 'D556677889', '321 Ho Man Tin', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('renter', 'David Chan', 'davidchan@gmail.com', 'E998877665', '654 To Kwa Wan', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('owner', 'Amy Lam', 'amylam@gmail.com', 'F112233445', '78 Mong Kok', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('owner', 'Billy Chan', 'billychan@gmail.com', 'G556677889', '32 Ho Man Tin', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('owner', 'Cherry Chan', 'cherrychan@gmail.com', 'H998877665', '65 To Kwa Wan', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('renter', 'Daniel Lam', 'daniellam@gmail.com', 'I112233445', '89 Mong Kok', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('renter', 'Ethan Chan', 'ethanchan@gmail.com', 'J556677889', '21 Ho Man Tin', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW()),
('renter', 'Gigi Chan', 'gigichan@gmail.com', 'K998877665', '64 To Kwa Wan', '$2b$12$Trr9TQ/II2Ay6viRrcqZy.rWKhGU7GwyDM5dpmJhHPHTgJOqPv/uq', 'active', NOW(), NOW());

-- Insert Owner table data (5 records)
-- Car owners with their user IDs and ratings (1-5 scale)
INSERT INTO Owner (user_id, rating, verificationStatus) VALUES
(3, 4.5, 'approved'),
(4, 4.3, 'approved'),
(6, 4.2, 'pending'),
(7, 4.9, 'approved'),
(8, 3.2, 'pending');


-- Insert Renter table data (5 records)
-- Renters with their user IDs, ratings, and account balances
INSERT INTO Renter (user_id, rating, balance) VALUES
(2, 4.3, 250.00),
(5, 4.9, 500.00),
(9, 4.2, 0.00),
(10, 2.0, 250.00),
(11, 4.7, 1000.00);

-- Insert Insurance table data (5 records)
-- Different insurance plans available for vehicle rentals
INSERT INTO Insurance (types, fee, validityPeriod, company, description) VALUES
('Basic Coverage', 15.00, '1 year', 'Geico', 'Basic liability coverage for rental vehicles'),
('Full Coverage', 25.00, '1 year', 'State Farm', 'Comprehensive insurance with collision protection'),
('Premium Protection', 35.00, '6 months', 'Allstate', 'Premium coverage including roadside assistance'),
('Minimum Liability', 10.00, '1 year', 'Progressive', 'State minimum liability insurance'),
('Extended Warranty', 20.00, '2 years', 'Liberty Mutual', 'Extended mechanical breakdown coverage');

-- Insert additional Vehicle table data (15 records)
-- More vehicles with different types, brands, and rental statuses
INSERT INTO Vehicle (owner_id, carType, lisenceNum, year, seatNum, status, photoURL, registerTime, dailyPrice, brand, model, location, description, verificationStatus) VALUES
(1, 'SUV', 'AB1234', 2022, 5, 'available', 'https://example.com/rav4.jpg', '2023-03-15 09:00:00', 380.00, 'Toyota', 'RAV4', 'Kowloon', 'Reliable SUV with low mileage', 'approved'),
(1, 'Sedan', 'CD5678', 2021, 5, 'rented', 'https://example.com/civic.jpg', '2023-04-20 10:30:00', 320.00, 'Honda', 'Civic', 'Mong Kok', 'Fuel efficient sedan in excellent condition', 'approved'),
(2, 'MPV', 'EF9012', 2023, 7, 'available', 'https://example.com/alphard.jpg', '2023-05-10 14:15:00', 450.00, 'Toyota', 'Alphard', 'Ho Man Tin', 'Luxury MPV for family trips', 'approved'),
(2, 'Sports Car', 'GH3456', 2022, 2, 'available', 'https://example.com/911.jpg', '2023-06-05 11:45:00', 680.00, 'Porsche', '911', 'Ho Man Tin', 'High-performance sports car', 'pending'),
(3, 'Hatchback', 'IJ7890', 2020, 5, 'maintenance', 'https://example.com/mazda3.jpg', '2023-02-28 16:20:00', 280.00, 'Mazda', 'Mazda3', 'Mong Kok', 'Compact car perfect for city driving', 'approved'),
(3, 'SUV', 'KL1234', 2023, 5, 'available', 'https://example.com/cx5.jpg', '2023-07-12 08:45:00', 420.00, 'Mazda', 'CX-5', 'To Kwa Wan', 'Spacious SUV with premium features', 'approved'),
(4, 'Sedan', 'MN5678', 2022, 5, 'available', 'https://example.com/camry.jpg', '2023-08-18 13:20:00', 350.00, 'Toyota', 'Camry', 'Ho Man Tin', 'Comfortable sedan for business trips', 'approved'),
(4, 'Coupe', 'OP9012', 2021, 4, 'rented', 'https://example.com/bmw4.jpg', '2023-09-22 15:30:00', 520.00, 'BMW', '4 Series', 'Kowloon', 'Stylish coupe with great handling', 'approved'),
(5, 'Minivan', 'QR3456', 2020, 8, 'available', 'https://example.com/odyssey.jpg', '2023-10-05 11:10:00', 400.00, 'Honda', 'Odyssey', 'Mong Kok', 'Perfect for large families', 'pending'),
(5, 'SUV', 'ST7890', 2023, 7, 'available', 'https://example.com/highlander.jpg', '2023-11-15 09:45:00', 480.00, 'Toyota', 'Highlander', 'To Kwa Wan', 'Reliable 7-seater SUV', 'approved'),
(1, 'Electric', 'UV1234', 2023, 5, 'available', 'https://example.com/model3.jpg', '2023-12-03 14:25:00', 550.00, 'Tesla', 'Model 3', 'Kowloon', 'Eco-friendly electric vehicle', 'approved'),
(2, 'Luxury Sedan', 'WX5678', 2022, 5, 'available', 'https://example.com/es300.jpg', '2024-01-10 10:15:00', 600.00, 'Lexus', 'ES 300h', 'Ho Man Tin', 'Premium luxury sedan', 'pending'),
(3, 'Convertible', 'YZ9012', 2021, 4, 'maintenance', 'https://example.com/mx5.jpg', '2024-02-14 16:40:00', 450.00, 'Mazda', 'MX-5', 'Mong Kok', 'Fun convertible for weekend drives', 'approved'),
(4, 'Sports Car', 'ZA3456', 2023, 2, 'available', 'https://example.com/supra.jpg', '2024-03-20 12:30:00', 650.00, 'Toyota', 'Supra', 'Kowloon', 'Powerful sports car with great performance', 'approved'),
(5, 'Compact SUV', 'BC7890', 2022, 5, 'available', 'https://example.com/chr.jpg', '2024-04-25 08:50:00', 380.00, 'Toyota', 'C-HR', 'To Kwa Wan', 'Stylish compact SUV for urban driving', 'approved');

-- 插入 Rental 表格數據（15筆）
-- Order statuses aligned with backend: pending/confirmed/active/completed/cancelled
-- Payment statuses aligned with backend: paid/unpaid
INSERT INTO Rental (vehicle_id, renter_id, rentalStartTime, rentalEndTime, totalAmount, orderStatus, paymentStatus, returnTime, dailyPrice, createTime, insurance_id) VALUES
(2, 1, '2024-01-05 10:00:00', '2024-01-08 18:00:00', 960.00, 'completed', 'paid', '2024-01-08 17:30:00', 320.00, '2024-01-01 14:20:00', 1),
(1, 2, '2024-02-10 09:00:00', '2024-02-15 20:00:00', 1900.00, 'active', 'paid', NULL, 380.00, '2024-02-05 11:15:00', 2),
(3, 3, '2024-01-15 08:00:00', '2024-01-17 19:00:00', 900.00, 'completed', 'paid', '2024-01-17 18:45:00', 450.00, '2024-01-10 16:40:00', 3),
(4, 4, '2024-02-20 11:00:00', '2024-02-25 21:00:00', 3400.00, 'pending', 'unpaid', NULL, 680.00, '2024-02-15 13:25:00', 4),
(5, 5, '2024-01-25 09:30:00', '2024-01-27 17:00:00', 560.00, 'completed', 'paid', '2024-01-27 16:15:00', 280.00, '2024-01-20 15:50:00', 5),
(6, 1, '2024-03-01 08:00:00', '2024-03-05 19:00:00', 1680.00, 'completed', 'paid', '2024-03-05 18:30:00', 420.00, '2024-02-25 10:30:00', 1),
(7, 2, '2024-03-10 10:00:00', '2024-03-12 20:00:00', 700.00, 'active', 'paid', NULL, 350.00, '2024-03-05 14:20:00', 2),
(8, 3, '2024-02-15 09:00:00', '2024-02-20 18:00:00', 2600.00, 'completed', 'paid', '2024-02-20 17:45:00', 520.00, '2024-02-10 11:45:00', 3),
(9, 4, '2024-03-18 07:30:00', '2024-03-25 21:00:00', 2800.00, 'pending', 'unpaid', NULL, 400.00, '2024-03-12 16:10:00', 4),
(10, 5, '2024-02-28 08:00:00', '2024-03-02 19:00:00', 1440.00, 'completed', 'paid', '2024-03-02 18:15:00', 480.00, '2024-02-22 13:35:00', 5),
(11, 1, '2024-03-22 10:00:00', '2024-03-24 20:00:00', 1100.00, 'pending', 'paid', NULL, 550.00, '2024-03-18 09:25:00', 1),
(12, 2, '2024-02-10 08:30:00', '2024-02-14 19:00:00', 2400.00, 'completed', 'paid', '2024-02-14 18:30:00', 600.00, '2024-02-05 15:40:00', 2),
(13, 3, '2024-03-25 09:00:00', '2024-03-27 18:00:00', 900.00, 'pending', 'unpaid', NULL, 450.00, '2024-03-20 12:15:00', 3),
(14, 4, '2024-02-05 11:00:00', '2024-02-08 20:00:00', 1950.00, 'completed', 'paid', '2024-02-08 19:45:00', 650.00, '2024-01-30 14:50:00', 4),
(15, 5, '2024-03-15 08:00:00', '2024-03-18 19:00:00', 1140.00, 'active', 'paid', NULL, 380.00, '2024-03-10 10:20:00', 5);

-- Insert Rental table data (15 records)
-- Rental orders with different statuses: completed, active, upcoming
INSERT INTO RentalInsurance (rental_id, insurance_id, PolicyNumer, effectiveDate) VALUES
(1, 1, 'HKA123456789', '2024-01-05'),
(2, 2, 'HKB987654321', '2024-02-10'),
(3, 3, 'HKC456789123', '2024-01-15'),
(4, 4, 'HKD789123456', '2024-02-20'),
(5, 5, 'HKE321654987', '2024-01-25'),
(6, 1, 'HKF654987321', '2024-03-01'),
(7, 2, 'HKG789123654', '2024-03-10'),
(8, 3, 'HKH123789456', '2024-02-15'),
(9, 4, 'HKI456123789', '2024-03-18'),
(10, 5, 'HKJ789456123', '2024-02-28'),
(11, 1, 'HKK321987654', '2024-03-22'),
(12, 2, 'HKL654321987', '2024-02-10'),
(13, 3, 'HKM987654123', '2024-03-25'),
(14, 4, 'HKN123987456', '2024-02-05'),
(15, 5, 'HKO456789321', '2024-03-15');

-- Insert RentalInsurance table data (15 records)
-- Insurance policies linked to each rental order with policy numbers and effective dates
INSERT INTO Payment (rental_id, paymentAmount, paymentMethod, paymentTime, TransactionNumber, paymentStatus) VALUES
(1, 960.00, 'credit_card', '2024-01-01 14:25:00', 'HK001234567', 'paid'),
(2, 1900.00, 'debit_card', '2024-02-05 11:20:00', 'HK002345678', 'paid'),
(3, 900.00, 'paypal', '2024-01-10 16:45:00', 'HK003456789', 'paid'),
(4, 3400.00, 'credit_card', '2024-02-15 13:30:00', 'HK004567890', 'pending'),
(5, 560.00, 'bank_transfer', '2024-01-20 15:55:00', 'HK005678901', 'paid'),
(6, 1680.00, 'credit_card', '2024-02-25 10:35:00', 'HK006789012', 'paid'),
(7, 700.00, 'debit_card', '2024-03-05 14:25:00', 'HK007890123', 'paid'),
(8, 2600.00, 'paypal', '2024-02-10 11:50:00', 'HK008901234', 'paid'),
(9, 2800.00, 'credit_card', '2024-03-12 16:15:00', 'HK009012345', 'pending'),
(10, 1440.00, 'bank_transfer', '2024-02-22 13:40:00', 'HK010123456', 'paid'),
(11, 1100.00, 'credit_card', '2024-03-18 09:30:00', 'HK011234567', 'paid'),
(12, 2400.00, 'debit_card', '2024-02-05 15:45:00', 'HK012345678', 'paid'),
(13, 900.00, 'paypal', '2024-03-20 12:20:00', 'HK013456789', 'pending'),
(14, 1950.00, 'credit_card', '2024-01-30 14:55:00', 'HK014567890', 'paid'),
(15, 1140.00, 'bank_transfer', '2024-03-10 10:25:00', 'HK015678901', 'paid');