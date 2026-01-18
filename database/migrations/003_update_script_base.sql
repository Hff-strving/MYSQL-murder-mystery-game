/*==============================================================*/
/* 基础剧本信息同步脚本                                          */
/* 目的：将 t_script 的标题/人数配置 与 最新12本剧本保持一致       */
/* 可重复执行：仅使用 UPDATE，不删除原有数据                      */
/*==============================================================*/

-- 确保使用正确的数据库后再执行本脚本

-- 硬核推理
UPDATE t_script SET Title='年轮', Min_Players=5, Max_Players=5 WHERE Script_ID=1001;
UPDATE t_script SET Title='漓川怪谈簿', Min_Players=7, Max_Players=7 WHERE Script_ID=1002;
UPDATE t_script SET Title='极夜', Min_Players=6, Max_Players=6 WHERE Script_ID=1003;

-- 情感沉浸
UPDATE t_script SET Title='云使', Min_Players=7, Max_Players=7 WHERE Script_ID=1004;
UPDATE t_script SET Title='告别诗', Min_Players=6, Max_Players=6 WHERE Script_ID=1005;
UPDATE t_script SET Title='就像水消失在水中', Min_Players=6, Max_Players=6 WHERE Script_ID=1006;

-- 欢乐机制
UPDATE t_script SET Title='搞钱', Min_Players=7, Max_Players=7 WHERE Script_ID=1007;
UPDATE t_script SET Title='青楼', Min_Players=7, Max_Players=7 WHERE Script_ID=1008;
UPDATE t_script SET Title='刀鞘', Min_Players=7, Max_Players=7 WHERE Script_ID=1009;

-- 惊悚/IP
UPDATE t_script SET Title='古董局中局', Min_Players=7, Max_Players=7 WHERE Script_ID=1010;
UPDATE t_script SET Title='桃花源记', Min_Players=7, Max_Players=7 WHERE Script_ID=1011;
UPDATE t_script SET Title='一点半', Min_Players=6, Max_Players=6 WHERE Script_ID=1012;

-- 再次统一分类（与 profile 一致）
UPDATE t_script SET Type='硬核推理' WHERE Script_ID IN (1001,1002,1003);
UPDATE t_script SET Type='情感沉浸' WHERE Script_ID IN (1004,1005,1006);
UPDATE t_script SET Type='欢乐机制' WHERE Script_ID IN (1007,1008,1009);
UPDATE t_script SET Type='惊悚IP'  WHERE Script_ID IN (1010,1011,1012);

-- 验证
SELECT Script_ID, Title, Min_Players, Max_Players, Type
FROM t_script
WHERE Script_ID BETWEEN 1001 AND 1012
ORDER BY Script_ID;
