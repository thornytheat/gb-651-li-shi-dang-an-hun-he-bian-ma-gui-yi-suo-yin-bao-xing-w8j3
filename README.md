# 历史档案混合编码归一与索引保形

        面向一线复核人员的单服务数据工作台。样例数据随仓库提供，结论保留行号、原因码和原值。

        ## 业务模块

        - M1 文件采信：`/api/intake/run`
- M2 编码判定：`/api/encoding/detect`
- M3 字段保形：`/api/fields/normalize`
- M4 内容归一：`/api/content/normalize`
- M5 索引对账：`/api/reconcile`
- M6 批次导出：`/api/export/evidence.csv`

        ## 核心规则

        候选解码必须完整且无替换字符；档号、盒号与超大流水号始终按字符串逐字保留。题名可跨行；破损引号段按行号区间隔离留证，可确认的后续记录照常采信，同一批重跑不重复收档。

        ## 启动

        ```bash
        docker compose up --build
        ```

        浏览器访问 `http://localhost:18210`。运行测试：

        ```bash
        docker compose exec -T app pytest -q
        ```

        ## 样例流程

        依次运行六个模块；最后在批次页复核输入、有效、隔离与输出合计。同一输入摘要重复执行时复用原 `run_id`。

        ## 已知不覆盖

        不处理加密文件与需要外部密钥的对象；不连接真实生产存储。
