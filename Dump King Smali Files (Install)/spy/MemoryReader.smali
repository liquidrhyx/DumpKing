.class public Lcom/spy/MemoryReader;
.super Ljava/lang/Object;

.method public static readBytes(JI)[B
    .locals 10
    
    new-array v0, p2, [B
    
    :try_start
    # Open /proc/self/mem
    new-instance v1, Ljava/io/RandomAccessFile;
    const-string v2, "/proc/self/mem"
    const-string v3, "r"
    invoke-direct {v1, v2, v3}, Ljava/io/RandomAccessFile;-><init>(Ljava/lang/String;Ljava/lang/String;)V
    
    # Seek to address
    invoke-virtual {v1, p0, p1}, Ljava/io/RandomAccessFile;->seek(J)V
    
    # Read bytes
    invoke-virtual {v1, v0}, Ljava/io/RandomAccessFile;->read([B)I
    
    # Close file
    invoke-virtual {v1}, Ljava/io/RandomAccessFile;->close()V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    
    return-object v0
    
    :catch_all
    move-exception v1
    # Return empty array on error
    const/4 v2, 0x0
    new-array v0, v2, [B
    return-object v0
.end method

.method public static readInt(J)I
    .locals 4
    
    const/4 v0, 0x4
    invoke-static {p0, p1, v0}, Lcom/spy/MemoryReader;->readBytes(JI)[B
    move-result-object v0
    
    array-length v1, v0
    const/4 v2, 0x4
    if-ge v1, v2, :convert
    
    const/4 v1, 0x0
    return v1
    
    :convert
    # Convert 4 bytes to int (little endian)
    const/4 v1, 0x0
    aget-byte v1, v0, v1
    and-int/lit16 v1, v1, 0xff
    
    const/4 v2, 0x1
    aget-byte v2, v0, v2
    and-int/lit16 v2, v2, 0xff
    shl-int/lit8 v2, v2, 0x8
    or-int/2addr v1, v2
    
    const/4 v2, 0x2
    aget-byte v2, v0, v2
    and-int/lit16 v2, v2, 0xff
    shl-int/lit8 v2, v2, 0x10
    or-int/2addr v1, v2
    
    const/4 v2, 0x3
    aget-byte v2, v0, v2
    and-int/lit16 v2, v2, 0xff
    shl-int/lit8 v2, v2, 0x18
    or-int/2addr v1, v2
    
    return v1
.end method

.method public static writeInt(JI)Z
    .locals 6
    
    :try_start
    new-instance v0, Ljava/io/RandomAccessFile;
    const-string v1, "/proc/self/mem"
    const-string v2, "rw"
    invoke-direct {v0, v1, v2}, Ljava/io/RandomAccessFile;-><init>(Ljava/lang/String;Ljava/lang/String;)V
    
    invoke-virtual {v0, p0, p1}, Ljava/io/RandomAccessFile;->seek(J)V
    
    const/4 v1, 0x4
    new-array v1, v1, [B
    
    and-int/lit16 v2, p2, 0xff
    int-to-byte v2, v2
    const/4 v3, 0x0
    aput-byte v2, v1, v3
    
    shr-int/lit8 v2, p2, 0x8
    and-int/lit16 v2, v2, 0xff
    int-to-byte v2, v2
    const/4 v3, 0x1
    aput-byte v2, v1, v3
    
    shr-int/lit8 v2, p2, 0x10
    and-int/lit16 v2, v2, 0xff
    int-to-byte v2, v2
    const/4 v3, 0x2
    aput-byte v2, v1, v3
    
    shr-int/lit8 v2, p2, 0x18
    and-int/lit16 v2, v2, 0xff
    int-to-byte v2, v2
    const/4 v3, 0x3
    aput-byte v2, v1, v3
    
    invoke-virtual {v0, v1}, Ljava/io/RandomAccessFile;->write([B)V
    invoke-virtual {v0}, Ljava/io/RandomAccessFile;->close()V
    
    const/4 v0, 0x1
    return v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all
    
    :catch_all
    const/4 v0, 0x0
    return v0
.end method
