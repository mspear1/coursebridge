use coursebridge_db;

drop table if exists `comment`; 
drop table if exists `post`;
drop table if exists `student`;


CREATE TABLE `student` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  email_address varchar(35),
  unique(email_address),
  index(email_address),
  `hashed` varchar(70), 
  `phone_num` varchar(12),
  `name` varchar(40),
  `major1` ENUM ('Undecided', 'Africana_Studies', 'American_Studies', 'Anthropology', 'Art', 'Astronomy', 'Biological_Sciences', 'Chemistry', 'Classical_Civilization', 'Classical_Studies', 'Cognitive_and_Linguistic_Science', 'Computer_Science', 'East_Asian_Languages_and_Cultures', 'Economics', 'Education', 'English_and_Creative_Writing', 'Environmental_Studies', 'French_and_Francophone_Studies', 'Geosciences', 'German_Studies', 'History', 'Italian_Studies', 'Language_Studies_Linguistics', 'Mathematics', 'Music', 'Neuroscience', 'Philosophy', 'Physics', 'Political_Science', 'Psychology', 'Religion', 'Russian', 'Sociology', 'Spanish_and_Portuguese', 'Womens_and_Gender_Studies', 'Other'),
  `major2_minor` ENUM ('Undecided', 'Africana_Studies', 'American_Studies', 'Anthropology', 'Art', 'Astronomy', 'Biological_Sciences', 'Chemistry', 'Classical_Civilization', 'Classical_Studies', 'Cognitive_and_Linguistic_Science', 'Computer_Science', 'East_Asian_Languages_and_Cultures', 'Economics', 'Education', 'English_and_Creative_Writing', 'Environmental_Studies', 'French_and_Francophone_Studies', 'Geosciences', 'German_Studies', 'History', 'Italian_Studies', 'Language_Studies_Linguistics', 'Mathematics', 'Music', 'Neuroscience', 'Philosophy', 'Physics', 'Political_Science', 'Psychology', 'Religion', 'Russian', 'Sociology', 'Spanish_and_Portuguese', 'Womens_and_Gender_Studies', 'Other') COMMENT 'null if no input (optional), can enter 2nd major or minor',
  `dorm_hall` varchar(20),
  `profile_pic` varchar(30) COMMENT 'stores the file path to the picture on the server'
);


CREATE TABLE `post` (
  `pid` integer PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(30),
  `description` varchar(500),
  `tag` ENUM ('discuss_hw', 'social', 'study_session') COMMENT 'category/tag of the post',
  `location` varchar(50) COMMENT 'General location name',
  `timestamp` DateTime COMMENT 'Date posted',
  `status` ENUM ('open', 'closed'),
  `date` DateTime,
  `professor` varchar(50) COMMENT 'null if not a Discuss HW post',
  `class` varchar(8) COMMENT 'null if not a Discuss HW post; format: CourseName_#',
  `on_campus` ENUM ('yes', 'no') COMMENT 'null if not a social post',
  `sid` integer COMMENT 'fk, pid of post, null if no posts created yet'
);


CREATE TABLE `comment` (
  `cid` integer PRIMARY KEY AUTO_INCREMENT,
  `description` varchar(500),
  `sid` integer COMMENT 'id of student author',
  `timestamp` DateTime COMMENT 'Date posted',
  `pid` integer COMMENT 'fk, many comments to one post'
);


ALTER TABLE `post` ADD FOREIGN KEY (`sid`) REFERENCES `student` (`id`) on update cascade on delete restrict;


ALTER TABLE `comment` ADD FOREIGN KEY (`sid`) REFERENCES `student` (`id`) on update cascade on delete restrict;


ALTER TABLE `comment` ADD FOREIGN KEY (`pid`) REFERENCES `post` (`pid`) on update cascade on delete cascade;




use coursebridge_db;


insert into student(email_address, `hashed`, phone_num, `name`, major1, dorm_hall) 
values ('ms112@wellesley.edu', 'pswrd1', 2543687313, 'Madelynn Spear', 'Computer_Science','Tower Court East');

insert into student(email_address, `hashed`, phone_num, `name`, major1, dorm_hall)
values('gs109@wellesley.edu', 'hap12', 3399996702, 'Emily Suh', 'Computer_Science', 'Freeman');

insert into student(email_address, `hashed`, phone_num, `name`, major1, dorm_hall)
values ('hw102@wellesley.edu', 'pw123', 2026767066, 'Louisa Wang', 'Mathematics', Null);


insert into post(`title`, `description`, tag, `location`, `status`, `date`, on_campus, `sid`) values ('ice cream', 'get ice cream with me', 'social', 'JP Licks','open','2023-10-31', 'no', 1);


insert into post(`title`, `description`, tag, `location`, `timestamp`, `status`, `date`, on_campus, `sid`) values ('socialize', 'reach out to me if you want to talk!', 'social', 'tower court', '2023-10-31', 'closed', '2023-11-13', 'yes', 2);

insert into post(`title`, `description`, tag, `location`, `timestamp`, `status`, `date`, professor, class, on_campus, `sid`) values ('title', 'test2', 'discuss_hw', 'Science center', '2023-11-01', 'open', '2023-11-03', 'Professor Trenk', 'MATH 225', 'yes', 3);

insert into comment(`description`, `sid`, `timestamp`, pid)
values('I can go', 1, '2023-10-31 00:00:00', 1);


