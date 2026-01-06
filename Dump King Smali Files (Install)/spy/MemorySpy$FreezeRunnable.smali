.class public Lcom/spy/MemorySpy$FreezeRunnable;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public run()V
    .locals 4

    :loop_start
    sget-boolean v0, Lcom/spy/MemorySpy;->isFreezing:Z
    if-nez v0, :continue
    return-void

    :continue
    :try_start
    sget-wide v0, Lcom/spy/MemorySpy;->freezeAddress:J
    sget v2, Lcom/spy/MemorySpy;->freezeValue:I
    invoke-static {v0, v1, v2}, Lcom/spy/MemoryReader;->writeInt(JI)Z

    const-wide/16 v0, 0x64
    invoke-static {v0, v1}, Ljava/lang/Thread;->sleep(J)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_ex

    :catch_ex
    goto :loop_start
.end method
