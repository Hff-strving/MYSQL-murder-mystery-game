-- =====================================================
-- 剧本档案表迁移脚本（符合3NF规范）
-- 版本：002
-- 日期：2025-12-28
-- 说明：将剧本的详细配置信息从 t_script 分离到独立表
--       便于维护和扩展，符合数据库设计规范
-- =====================================================

-- 1. 创建剧本档案表（如果不存在）
CREATE TABLE IF NOT EXISTS t_script_profile (
    Script_ID BIGINT PRIMARY KEY COMMENT '剧本ID（主键，外键关联t_script）',
    Group_Category VARCHAR(50) NOT NULL COMMENT '大分类：硬核推理/情感沉浸/欢乐机制/惊悚IP',
    Sub_Category VARCHAR(100) DEFAULT NULL COMMENT '子分类标签：科幻/变格/新手/阵营等',
    Difficulty TINYINT NOT NULL DEFAULT 3 COMMENT '难度等级：1-5星',
    Duration_Min_Minutes INT NOT NULL COMMENT '最短时长（分钟）',
    Duration_Max_Minutes INT NOT NULL COMMENT '最长时长（分钟）',
    Gender_Config VARCHAR(50) NOT NULL COMMENT '性别配置：如"2男3女""性别不限""6-8浮动"',
    Allow_Gender_Bend TINYINT(1) DEFAULT 1 COMMENT '是否允许反串：0-否，1-是',
    Synopsis TEXT NOT NULL COMMENT '剧本简介',
    Create_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    Update_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_script_profile_script
        FOREIGN KEY (Script_ID) REFERENCES t_script(Script_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='剧本档案表（3NF设计）';

-- 2. 更新 t_script 表的 Type 字段为统一分类（保持向后兼容）
UPDATE t_script SET Type = '硬核推理' WHERE Script_ID = 1001;
UPDATE t_script SET Type = '硬核推理' WHERE Script_ID = 1002;
UPDATE t_script SET Type = '硬核推理' WHERE Script_ID = 1003;
UPDATE t_script SET Type = '情感沉浸' WHERE Script_ID = 1004;
UPDATE t_script SET Type = '情感沉浸' WHERE Script_ID = 1005;
UPDATE t_script SET Type = '情感沉浸' WHERE Script_ID = 1006;
UPDATE t_script SET Type = '欢乐机制' WHERE Script_ID = 1007;
UPDATE t_script SET Type = '欢乐机制' WHERE Script_ID = 1008;
UPDATE t_script SET Type = '欢乐机制' WHERE Script_ID = 1009;
UPDATE t_script SET Type = '惊悚IP' WHERE Script_ID = 1010;
UPDATE t_script SET Type = '惊悚IP' WHERE Script_ID = 1011;
UPDATE t_script SET Type = '惊悚IP' WHERE Script_ID = 1012;

-- 3. 插入/更新剧本档案数据（可重复执行）
INSERT INTO t_script_profile
(Script_ID, Group_Category, Sub_Category, Difficulty, Duration_Min_Minutes, Duration_Max_Minutes,
 Gender_Config, Allow_Gender_Bend, Synopsis)
VALUES
-- 1001 年轮
(1001, '硬核推理', '数学逻辑', 5, 270, 330, '2男3女', 1,
 '偏远山村王村，破损日记还原，多年恩怨，数学逻辑"计算"诡计，反转压迫感。'),

-- 1002 漓川怪谈簿
(1002, '硬核推理', '设定推理/变格', 4, 300, 360, '3男4女', 1,
 '日式和风，妖怪传说与密室案并存，在承认妖怪规则下推理，治愈结局。'),

-- 1003 极夜
(1003, '硬核推理', '科幻', 5, 300, 360, '4男2女', 1,
 '北极科考站极夜，通讯中断连环死亡，完美不在场证明，科幻设定+硬核诡计。'),

-- 1004 云使
(1004, '情感沉浸', '两世情缘', 3, 270, 300, '3男4女', 1,
 '两世情缘，书信机制，寻找记忆与羁绊，爱与牺牲。'),

-- 1005 告别诗
(1005, '情感沉浸', '新手友好', 2, 240, 270, '3男3女', 1,
 '校园青春，暗恋错过成长，告别仪式沉浸强。'),

-- 1006 就像水消失在水中
(1006, '情感沉浸', '文艺/刑侦', 3, 270, 300, '3男3女', 1,
 '旧案穿插今昔，冷峻文字，成年人的压抑与无奈。'),

-- 1007 搞钱
(1007, '欢乐机制', '博弈', 2, 240, 300, '性别不限', 1,
 '社区众人搞钱，投资诈骗结婚等爆笑博弈，结算首富为王。'),

-- 1008 青楼
(1008, '欢乐机制', '撕逼/戏精', 3, 240, 300, '3男4女', 1,
 '古代玉满楼，才艺比拼/拉帮结派/交易，势力角逐反转。'),

-- 1009 刀鞘
(1009, '欢乐机制', '阵营/谍战', 4, 300, 360, '4男3女', 1,
 '建国前夕监狱，多方势力审讯搜证私聊，找特务"刀鞘"完成阵营任务。'),

-- 1010 古董局中局
(1010, '惊悚IP', '授权IP/机制还原', 3, 240, 300, '6-8浮动', 1,
 '佛头案，鉴宝世家博弈，古董知识与江湖规矩，拍卖对抗。'),

-- 1011 桃花源记
(1011, '惊悚IP', '微恐/变格', 4, 270, 300, '4男3女', 1,
 '现代人误入桃花源，祭祀与诡异真相，惊悚搜证氛围强。'),

-- 1012 一点半
(1012, '惊悚IP', '恐怖', 3, 240, 300, '3男3女', 1,
 '见鬼游戏引发怪事递进心理恐怖，推理同时防背后凉意。')

ON DUPLICATE KEY UPDATE
    Group_Category = VALUES(Group_Category),
    Sub_Category = VALUES(Sub_Category),
    Difficulty = VALUES(Difficulty),
    Duration_Min_Minutes = VALUES(Duration_Min_Minutes),
    Duration_Max_Minutes = VALUES(Duration_Max_Minutes),
    Gender_Config = VALUES(Gender_Config),
    Allow_Gender_Bend = VALUES(Allow_Gender_Bend),
    Synopsis = VALUES(Synopsis),
    Update_Time = CURRENT_TIMESTAMP;

-- 4. 验证数据
SELECT
    s.Script_ID,
    s.Title,
    s.Type,
    p.Group_Category,
    p.Sub_Category,
    p.Difficulty,
    CONCAT(p.Duration_Min_Minutes/60, '-', p.Duration_Max_Minutes/60, 'h') AS Duration,
    p.Gender_Config,
    LEFT(p.Synopsis, 30) AS Synopsis_Preview
FROM t_script s
LEFT JOIN t_script_profile p ON s.Script_ID = p.Script_ID
WHERE s.Script_ID BETWEEN 1001 AND 1012
ORDER BY s.Script_ID;

-- 执行完成提示
SELECT '✅ 剧本档案表迁移完成！12个剧本数据已更新。' AS Status;
