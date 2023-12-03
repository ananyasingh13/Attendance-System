CREATE DATABASE attendance;
USE attendance;

CREATE TABLE user (
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

INSERT INTO user VALUES('admin', '123');

CREATE TABLE att (
    name VARCHAR(255) NOT NULL,
    regno VARCHAR(255) NOT NULL PRIMARY KEY,
    branch VARCHAR(255) NOT NULL,
    lastatt VARCHAR(255) NOT NULL
);

-- INSERT INTO att VALUES('Elon Musk', '20BCE0001', 'ECE');
-- INSERT INTO att VALUES('Emily Blunt', '20BCE0002', 'CSE');
-- INSERT INTO att VALUES('Raunak Raj', '20BCE2948', 'CSE');
-- INSERT INTO att VALUES('Ananya Singh', '20BCE0785', 'CSE');