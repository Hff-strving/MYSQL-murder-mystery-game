-- Active: 1750211303684@@127.0.0.1@3306@剧本杀店务管理系统
/*==============================================================*/
/* DBMS name:      MySQL 5.0                                    */
/* Created on:     2025/12/26 17:18:40                          */
/*==============================================================*/


drop table if exists T_DM;

drop table if exists T_Lock_Record;

drop table if exists T_Order;

drop table if exists T_Player;

drop table if exists T_Room;

drop table if exists T_Schedule;

drop table if exists T_Script;

drop table if exists T_Transaction;

/*==============================================================*/
/* Table: T_DM                                                  */
/*==============================================================*/
create table T_DM
(
   DM_ID                bigint not null,
   Name                 varchar(50) not null,
   Phone                char(11) not null,
   Star_Level           int,
   primary key (DM_ID)
);

/*==============================================================*/
/* Table: T_Lock_Record                                         */
/*==============================================================*/
create table T_Lock_Record
(
   LockID               bigint not null,
   Schedule_ID          bigint not null,
   Player_ID            bigint not null,
   LockTime             timestamp not null,
   ExpireTime           timestamp not null,
   Status               int not null,
   primary key (LockID)
);

/*==============================================================*/
/* Table: T_Order                                               */
/*==============================================================*/
create table T_Order
(
   Order_ID             bigint not null,
   Player_ID            bigint not null,
   Schedule_ID          bigint not null,
   Amount               decimal(10,2) not null,
   Pay_Status           int not null,
   Verify_Code          varchar(10),
   Create_Time          timestamp not null,
   primary key (Order_ID)
);

/*==============================================================*/
/* Table: T_Player                                              */
/*==============================================================*/
create table T_Player
(
   Player_ID            bigint not null,
   Open_ID              varchar(64) not null,
   Nickname             varchar(50),
   Phone                char(11),
   primary key (Player_ID)
);

/*==============================================================*/
/* Table: T_Room                                                */
/*==============================================================*/
create table T_Room
(
   Room_ID              int not null,
   Room_Name            varchar(50) not null,
   Capacity             int,
   primary key (Room_ID)
);

/*==============================================================*/
/* Table: T_Schedule                                            */
/*==============================================================*/
create table T_Schedule
(
   Schedule_ID          bigint not null,
   Room_ID              int not null,
   Script_ID            bigint not null,
   DM_ID                bigint not null,
   Start_Time           timestamp not null,
   End_Time             timestamp,
   Status               int not null,
   Real_Price           decimal(10,2),
   primary key (Schedule_ID)
);

/*==============================================================*/
/* Table: T_Script                                              */
/*==============================================================*/
create table T_Script
(
   Script_ID            bigint not null,
   Title                varchar(100) not null,
   Type                 varchar(20),
   Min_Players          int not null,
   Max_Players          int not null,
   Duration             timestamp,
   Base_Price           decimal(10,2) not null,
   Status               int not null,
   primary key (Script_ID)
);

/*==============================================================*/
/* Table: T_Transaction                                         */
/*==============================================================*/
create table T_Transaction
(
   Trans_ID             bigint not null,
   Order_ID             bigint not null,
   Amount               decimal(10,2) not null,
   Trans_Type           int not null,
   Channel              int,
   Trans_Time           timestamp not null,
   Result               int not null,
   primary key (Trans_ID)
);

alter table T_Lock_Record add constraint FK_R_Player_Lock foreign key (Player_ID)
      references T_Player (Player_ID) on delete restrict on update restrict;

alter table T_Lock_Record add constraint FK_场次占用 foreign key (Schedule_ID)
      references T_Schedule (Schedule_ID) on delete restrict on update restrict;

alter table T_Order add constraint FK_R_Generate_Order foreign key (Schedule_ID)
      references T_Schedule (Schedule_ID) on delete restrict on update restrict;

alter table T_Order add constraint FK_R_Place_Order foreign key (Player_ID)
      references T_Player (Player_ID) on delete restrict on update restrict;

alter table T_Schedule add constraint FK_R_DM_Host foreign key (DM_ID)
      references T_DM (DM_ID) on delete restrict on update restrict;

alter table T_Schedule add constraint FK_R_Room_Use foreign key (Room_ID)
      references T_Room (Room_ID) on delete restrict on update restrict;

alter table T_Schedule add constraint FK_R_Script_Schedule foreign key (Script_ID)
      references T_Script (Script_ID) on delete restrict on update restrict;

alter table T_Transaction add constraint FK_产生 foreign key (Order_ID)
      references T_Order (Order_ID) on delete restrict on update restrict;

