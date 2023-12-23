
use coursebridge_db;

CREATE TABLE `phnum` (
  `nid` integer PRIMARY KEY AUTO_INCREMENT,
  `requester` integer COMMENT 'id of student requester',
  `approver` integer COMMENT 'id of student approver',
  `approved` ENUM ('yes', 'no')
);

ALTER TABLE `phnum` ADD FOREIGN KEY (`requester`) REFERENCES `student` (`id`) on update cascade on delete restrict;;

ALTER TABLE `phnum` ADD FOREIGN KEY (`approver`) REFERENCES `student` (`id`) on update cascade on delete restrict;;