# はじめに
このマニュアルは n8n を使用して、チャットメッセージをトリガーにAI Agentを介してMCPクライアントツールと連携するワークフローを作成する手順を説明します。

## 前提条件
- n8n がインストール済みであること
- OpenAIアカウントとAPIキーが設定済みであること
- MCPクライアントツールが利用可能な状態であること

## 手順概要
1. 新しいワークフローを作成します。
2. チャットメッセージ受信トリガーを設定します。
3. AI Agentノードを追加します。
4. OpenAI Chat ModelをAI Agentに接続します。
5. MCP Client ToolをAI Agentに接続し、エンドポイントを設定します。
6. ワークフローをテスト実行し、結果を確認します。

## 手順詳細

### 1. 新しいワークフローを作成します。
まず、n8nのダッシュボードから新しいワークフローを作成します。

ワークフローの作成ボタンをクリックします。

![ワークフローの作成](<step01_create_workflow.png>)
*図1: ワークフローの作成画面*

新しいワークフローの編集画面が表示されます。

![新しいワークフロー編集画面](<step02_new_workflow_editor.png>)
*図2: 新しいワークフロー編集画面*

### 2. チャットメッセージ受信トリガーを設定します。
次に、ワークフローの最初のステップとしてチャットメッセージ受信トリガーを設定します。

「最初のステップを追加」をクリックし、右側に表示されるトリガーリストから「チャットメッセージ」を選択します。

![チャットメッセージトリガーの選択](<step03_select_chat_message_trigger.png>)
*図3: チャットメッセージトリガーの選択*

トリガー設定画面が開いたら、特に設定を変更せず、右上の鉛筆アイコンをクリックして設定を保存し、閉じます。

![トリガー設定保存](<step04_save_trigger_settings.png>)
*図4: トリガー設定の保存*

「When chat message received」ノードがワークフローに追加されます。

![When chat message receivedノード](<step05_chat_message_received_node.png>)
*図5: When chat message receivedノード*

### 3. AI Agentノードを追加します。
「When chat message received」ノードの右側にある「+」ボタンをクリックし、次に「AI」カテゴリを展開し、「AI Agent」を選択します。

![AI Agentノードの追加](<step06_add_ai_agent_node.png>)
*図6: AI Agentノードの追加*

AI Agentノードの設定画面が開いたら、特に設定を変更せず、右上の鉛筆アイコンをクリックして設定を保存し、閉じます。

![AI Agent設定保存](<step07_save_ai_agent_settings.png>)
*図7: AI Agent設定の保存*

AI Agentノードがワークフローに追加されます。

![AI Agentノード](<step08_ai_agent_node_added.png>)
*図8: AI Agentノード*

### 4. OpenAI Chat ModelをAI Agentに接続します。
AI Agentノードの下にある「Chat Model」の「+」ボタンをクリックし、次に「Language Models」カテゴリを展開し、「OpenAI Chat Model」を選択します。

![OpenAI Chat Modelの選択](<step09_select_openai_chat_model.png>)
*図9: OpenAI Chat Modelの選択*

OpenAI Chat Modelの設定画面が開いたら、「Model」ドロップダウンから「gpt-4o」を選択します。

![gpt-4oの選択](<step10_select_gpt4o.png>)
*図10: gpt-4oの選択*

右上の鉛筆アイコンをクリックして設定を保存し、閉じます。

![OpenAI Chat Model設定保存](<step11_save_openai_chat_model_settings.png>)
*図11: OpenAI Chat Model設定の保存*

OpenAI Chat ModelがAI Agentに接続されます。

![AI AgentにOpenAI Chat Model接続](<step12_openai_chat_model_connected.png>)
*図12: AI AgentにOpenAI Chat Model接続*

### 5. MCP Client ToolをAI Agentに接続し、エンドポイントを設定します。
AI Agentノードの右側にある「Tool」の「+」ボタンをクリックし、次に「Tools」カテゴリを展開し、「MCP Client Tool」を選択します。

![MCP Client Toolの選択](<step13_select_mcp_client_tool.png>)
*図13: MCP Client Toolの選択*

MCP Client Toolの設定画面が開いたら、「Endpoint」フィールドに `http://127.0.0.1:5003/sse` と入力します。

![MCP Client Toolエンドポイント設定](<step14_set_mcp_client_endpoint.png>)
*図14: MCP Client Toolのエンドポイント設定*

右上の鉛筆アイコンをクリックして設定を保存し、閉じます。

![MCP Client Tool設定保存](<step15_save_mcp_client_tool_settings.png>)
*図15: MCP Client Tool設定の保存*

MCP Client ToolがAI Agentに接続されます。

![AI AgentにMCP Client Tool接続](<step16_mcp_client_tool_connected.png>)
*図16: AI AgentにMCP Client Tool接続*

### 6. ワークフローをテスト実行し、結果を確認します。
画面下部のチャット入力欄に「Kamakuraの天気を調べて」と入力し、送信ボタンをクリックします。

![チャットでテスト実行](<step17_chat_test_execution.png>)
*図17: チャットでのテスト実行*

ワークフローが実行され、チャットボットがMCP Client Toolを介して鎌倉の天気情報を取得し、返答します。

![ワークフロー実行結果](<step18_workflow_execution_result.png>)
*図18: ワークフロー実行結果*

これで、チャットメッセージをトリガーとしたAI AgentとMCPクライアントツール連携ワークフローの作成とテストが完了しました。
