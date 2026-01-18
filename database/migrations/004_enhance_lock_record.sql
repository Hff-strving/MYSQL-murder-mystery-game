/*==============================================================*/
/* 加强锁位记录表功能                                           */
/* 目的：支持锁位→下单→支付的完整流程展示                        */
/* 可重复执行：使用 IF NOT EXISTS 创建/补齐结构                   */
/*==============================================================*/

-- 确保 t_lock_record 表存在并与后端字段名一致（LockID/LockTime/ExpireTime）
CREATE TABLE IF NOT EXISTS t_lock_record (
    LockID BIGINT NOT NULL PRIMARY KEY COMMENT '锁定记录ID',
    Schedule_ID BIGINT NOT NULL COMMENT '场次ID',
    Player_ID BIGINT NOT NULL COMMENT '玩家ID',
    LockTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '锁定时间',
    ExpireTime DATETIME NOT NULL COMMENT '过期时间',
    Status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0=锁定中，1=已转订单，2=已释放，3=已过期',
    Order_ID BIGINT NULL COMMENT '关联订单ID（转订单后）',
    Create_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    Update_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (Schedule_ID) REFERENCES t_schedule(Schedule_ID),
    FOREIGN KEY (Player_ID) REFERENCES t_player(Player_ID),
    INDEX idx_schedule (Schedule_ID),
    INDEX idx_player (Player_ID),
    INDEX idx_status (Status),
    INDEX idx_expire (ExpireTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场次锁位记录表';

-- 验证表结构
SELECT
    'Lock Record Table Structure' AS Info,
    COUNT(*) AS Total_Locks
FROM t_lock_record;
