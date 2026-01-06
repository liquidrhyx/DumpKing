.class public Lcom/spy/MemorySpy$ServerRunnable;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public run()V
    .locals 7

    :try_start
    new-instance v0, Ljava/net/ServerSocket;
    const/16 v1, 0x3039
    invoke-direct {v0, v1}, Ljava/net/ServerSocket;-><init>(I)V

    :loop_start
    invoke-virtual {v0}, Ljava/net/ServerSocket;->accept()Ljava/net/Socket;
    move-result-object v1

    invoke-virtual {v1}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;
    move-result-object v2

    const/16 v3, 0x400
    new-array v3, v3, [B
    invoke-virtual {v2, v3}, Ljava/io/InputStream;->read([B)I
    move-result v4

    new-instance v5, Ljava/lang/String;
    const/4 v6, 0x0
    invoke-direct {v5, v3, v6, v4}, Ljava/lang/String;-><init>([BII)V

    invoke-static {v5}, Lcom/spy/MemorySpy;->processCommand(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v5

    invoke-virtual {v1}, Ljava/net/Socket;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v2
    invoke-virtual {v5}, Ljava/lang/String;->getBytes()[B
    move-result-object v3
    invoke-virtual {v2, v3}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {v2}, Ljava/io/OutputStream;->flush()V

    invoke-virtual {v1}, Ljava/net/Socket;->close()V

    goto :loop_start
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_ex

    :catch_ex
    return-void
.end method
