.class public Lcom/spy/MemorySpy;
.super Ljava/lang/Object;

.field private static freezeThread:Ljava/lang/Thread;
.field private static freezeAddress:J
.field private static freezeValue:I
.field private static isFreezing:Z

.method public static startServer()V
    .locals 2

    new-instance v0, Ljava/lang/Thread;
    new-instance v1, Lcom/spy/MemorySpy$ServerRunnable;
    invoke-direct {v1}, Lcom/spy/MemorySpy$ServerRunnable;-><init>()V
    invoke-direct {v0, v1}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    invoke-virtual {v0}, Ljava/lang/Thread;->start()V

    return-void
.end method

.method public static processCommand(Ljava/lang/String;)Ljava/lang/String;
    .locals 5

    # PING
    const-string v0, "PING"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_debug
    const-string v0, "PONG"
    return-object v0

    :check_debug
    # DEBUG
    const-string v0, "DEBUG"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_test

    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "DEBUG_OK|Maps:"
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-static {}, Lcom/spy/MemoryMap;->getMaps()Ljava/util/List;
    move-result-object v1
    invoke-interface {v1}, Ljava/util/List;->size()I
    move-result v1
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_test
    # TEST
    const-string v0, "TEST"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_scan

    :try_test
    const-wide/16 v0, 0x0
    const/4 v2, 0x4
    invoke-static {v0, v1, v2}, Lcom/spy/MemoryReader;->readBytes(JI)[B
    move-result-object v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "TEST_OK|ReadSize:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    array-length v2, v0
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
    :try_test_end
    .catch Ljava/lang/Exception; {:try_test .. :try_test_end} :test_error

    :test_error
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "TEST_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_scan
    # SCAN:value
    const-string v0, "SCAN:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_scan_hex

    :try_start_scan
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0
    const/4 v1, 0x1
    aget-object v0, v0, v1
    invoke-static {v0}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v0
    invoke-static {v0}, Lcom/spy/MemoryScanner;->scanInt(I)Ljava/util/List;
    move-result-object v0
    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end_scan
    .catch Ljava/lang/Exception; {:try_start_scan .. :try_end_scan} :error_scan
    return-object v0

    :error_scan
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "SCAN_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_scan_hex
    # SCAN_HEX:hexpattern (FIXED COMMAND NAME)
    const-string v0, "SCAN_HEX:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_read
    invoke-static {p0}, Lcom/spy/MemorySpy;->handleScanHex(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_read
    # READ:address:size
    const-string v0, "READ:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_write
    invoke-static {p0}, Lcom/spy/MemorySpy;->handleRead(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_write
    # WRITE:address:value
    const-string v0, "WRITE:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_write_hex
    invoke-static {p0}, Lcom/spy/MemorySpy;->handleWrite(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_write_hex
    # WRITE_HEX:address:hexdata (NEW)
    const-string v0, "WRITE_HEX:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_freeze
    invoke-static {p0}, Lcom/spy/MemorySpy;->handleWriteHex(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_freeze
    # FREEZE:address:value
    const-string v0, "FREEZE:"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_unfreeze
    invoke-static {p0}, Lcom/spy/MemorySpy;->handleFreeze(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_unfreeze
    # UNFREEZE
    const-string v0, "UNFREEZE"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :check_maps
    invoke-static {}, Lcom/spy/MemorySpy;->handleUnfreeze()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :check_maps
    # MAPS
    const-string v0, "MAPS"
    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :unknown
    invoke-static {}, Lcom/spy/MemoryMap;->getMaps()Ljava/util/List;
    move-result-object v0
    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :unknown
    const-string v0, "ERROR:Unknown command"
    return-object v0
.end method

.method public static handleRead(Ljava/lang/String;)Ljava/lang/String;
    .locals 8

    :try_start
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v1

    const/4 v2, 0x1
    aget-object v3, v1, v2
    const/4 v4, 0x2
    invoke-virtual {v3, v4}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v3
    const/16 v5, 0x10
    invoke-static {v3, v5}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v6

    aget-object v3, v1, v4
    invoke-static {v3}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v4

    invoke-static {v6, v7, v4}, Lcom/spy/MemoryReader;->readBytes(JI)[B
    move-result-object v0

    invoke-static {v0}, Lcom/spy/MemorySpy;->bytesToHex([B)Ljava/lang/String;
    move-result-object v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    return-object v0

    :catch_all
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "READ_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static handleWrite(Ljava/lang/String;)Ljava/lang/String;
    .locals 8

    :try_start
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v1

    const/4 v2, 0x1
    aget-object v3, v1, v2
    const/4 v4, 0x2
    invoke-virtual {v3, v4}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v3
    const/16 v5, 0x10
    invoke-static {v3, v5}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v6

    aget-object v3, v1, v4
    invoke-static {v3}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v4

    invoke-static {v6, v7, v4}, Lcom/spy/MemoryReader;->writeInt(JI)Z
    move-result v0

    if-eqz v0, :write_fail

    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "WRITE_OK:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    return-object v0

    :write_fail
    const-string v0, "WRITE_FAILED"
    return-object v0

    :catch_all
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "WRITE_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static handleWriteHex(Ljava/lang/String;)Ljava/lang/String;
    .locals 8

    :try_start
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v1

    const/4 v2, 0x1
    aget-object v3, v1, v2
    const/4 v4, 0x2
    invoke-virtual {v3, v4}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v3
    const/16 v5, 0x10
    invoke-static {v3, v5}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v6

    aget-object v3, v1, v4
    invoke-static {v3}, Lcom/spy/MemorySpy;->hexToBytes(Ljava/lang/String;)[B
    move-result-object v4

    invoke-static {v6, v7, v4}, Lcom/spy/MemoryReader;->writeBytes(J[B)Z
    move-result v0

    if-eqz v0, :write_fail
    const-string v0, "WRITE_OK"
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    return-object v0

    :write_fail
    const-string v0, "WRITE_FAILED"
    return-object v0

    :catch_all
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "WRITE_HEX_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static handleFreeze(Ljava/lang/String;)Ljava/lang/String;
    .locals 8

    :try_start
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v1

    const/4 v2, 0x1
    aget-object v3, v1, v2
    const/4 v4, 0x2
    invoke-virtual {v3, v4}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v3
    const/16 v5, 0x10
    invoke-static {v3, v5}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v6
    sput-wide v6, Lcom/spy/MemorySpy;->freezeAddress:J

    aget-object v3, v1, v4
    invoke-static {v3}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v4
    sput v4, Lcom/spy/MemorySpy;->freezeValue:I

    const/4 v0, 0x1
    sput-boolean v0, Lcom/spy/MemorySpy;->isFreezing:Z

    new-instance v0, Ljava/lang/Thread;
    new-instance v1, Lcom/spy/MemorySpy$FreezeRunnable;
    invoke-direct {v1}, Lcom/spy/MemorySpy$FreezeRunnable;-><init>()V
    invoke-direct {v0, v1}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    sput-object v0, Lcom/spy/MemorySpy;->freezeThread:Ljava/lang/Thread;
    invoke-virtual {v0}, Ljava/lang/Thread;->start()V

    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "FREEZE_OK:Freezing "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    sget-wide v1, Lcom/spy/MemorySpy;->freezeAddress:J
    invoke-static {v1, v2}, Ljava/lang/Long;->toHexString(J)Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, " to "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    sget v1, Lcom/spy/MemorySpy;->freezeValue:I
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    return-object v0

    :catch_all
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "FREEZE_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static handleUnfreeze()Ljava/lang/String;
    .locals 1

    const/4 v0, 0x0
    sput-boolean v0, Lcom/spy/MemorySpy;->isFreezing:Z
    const-string v0, "UNFREEZE_OK"
    return-object v0
.end method

.method public static handleScanHex(Ljava/lang/String;)Ljava/lang/String;
    .locals 3

    :try_start
    const-string v0, ":"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0

    const/4 v1, 0x1
    aget-object v0, v0, v1

    invoke-static {v0}, Lcom/spy/MemoryScanner;->scanHex(Ljava/lang/String;)Ljava/util/List;
    move-result-object v0
    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    return-object v0

    :catch_all
    move-exception v0
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "SCAN_HEX_ERROR:"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static bytesToHex([B)Ljava/lang/String;
    .locals 7

    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const/4 v1, 0x0
    array-length v2, p0

    :loop_start
    if-ge v1, v2, :loop_end

    aget-byte v3, p0, v1
    and-int/lit16 v3, v3, 0xff
    invoke-static {v3}, Ljava/lang/Integer;->toHexString(I)Ljava/lang/String;
    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/String;->length()I
    move-result v5
    const/4 v6, 0x1
    if-ne v5, v6, :append
    const-string v5, "0"
    invoke-virtual {v0, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    :append
    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    add-int/lit8 v1, v1, 0x1
    goto :loop_start

    :loop_end
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static hexToBytes(Ljava/lang/String;)[B
    .locals 6

    :try_start
    invoke-virtual {p0}, Ljava/lang/String;->length()I
    move-result v0
    const/4 v1, 0x2
    div-int/2addr v0, v1
    new-array v2, v0, [B

    const/4 v3, 0x0

    :loop_start
    if-ge v3, v0, :loop_end

    mul-int/lit8 v4, v3, 0x2
    add-int/lit8 v5, v4, 0x2
    invoke-virtual {p0, v4, v5}, Ljava/lang/String;->substring(II)Ljava/lang/String;
    move-result-object v4
    const/16 v5, 0x10
    invoke-static {v4, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
    move-result v4
    int-to-byte v4, v4
    aput-byte v4, v2, v3

    add-int/lit8 v3, v3, 0x1
    goto :loop_start

    :loop_end
    return-object v2
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all

    :catch_all
    const/4 v0, 0x0
    new-array v0, v0, [B
    return-object v0
.end method
