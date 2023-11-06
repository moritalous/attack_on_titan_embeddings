# Attack on Titan Embeddings on Bedrock

Create by Amazon Bedrock
![](image.png)


## デプロイ

1. LINE Messaging APIの設定
    1. [LINE Developers](https://developers.line.biz/)アカウントを作成します。
    1. [こちら](https://developers.line.biz/ja/docs/messaging-api/getting-started/)を参考にチャンネルを作成します。
    1. チャンネルシークレットと[長期のチャネルアクセストークン](https://developers.line.biz/ja/docs/basics/channel-access-token/#long-lived-channel-access-token)を取得します。


1. SAMのデプロイ

    1. ソースコードの取得

        ```shell
        git clone https://github.com/moritalous/attack_on_titan_embeddings.git
        ```

    1. ビルド

        ```
        sam build
        ```

    1. デプロイ

        ```
        sam deploy --guided
        ```

        パラメーターは以下の値をセットします。

        | パラメーター | 設定値 |
        | --- | --- |
        | LineChannelAccessToken | 長期のチャネルアクセストークン |
        | LineChannelSecret | チャンネルシークレット | 
        | NumOfHistory | チャット履歴の件数（デフォルト：10） |
        | FoundationModel | 使用する基盤モデル（anthropic.claude-v2、anthropic.claude-v1、anthropic.claude-instant-v1） |

        Webhookのリクエストを認証なしの関数URLで受信する設計にしているため、ウィザードの途中で`LineBotFunction Function Url has no authentication. Is this okay? [y/N]:`と聞かれますので、`Y`で回答する必要があります。

1. Lambdaの関数URLのURLをWebhook URLとしてLINE Messaging APIに設定。Webhookを有効化


## ベクトルデータベースの作成

[Notebook](shingeki_qdrant.ipynb)