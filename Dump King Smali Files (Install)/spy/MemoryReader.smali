.class public Lcom/spy/MemoryReader;
.super Ljava/lang/Object;

# Load our JNI bridge
.method static constructor <clinit>()V
    .locals 1

    const-string v0, "membridge"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    return-void
.end method

# JNI method (implemented in libmembridge.so)
.method private static native nativeReadMemory(JI[B)I
.end method

.method public static readBytes(JI)[B
    .locals 3

    # Allocate output buffer
    new-array v0, p2, [B

    :try_start
    invoke-static {p0, p1, p2, v0}, Lcom/spy/MemoryReader;->nativeReadMemory(JI[B)I
    move-result v1

    # if (bytesRead <= 0) return empty array
    if-lez v1, :fail

    return-object v0

    :fail
    const/4 v2, 0x0
    new-array v0, v2, [B
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :fail
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
    .locals 1
    const/4 v0, 0x0
    return v0
.end method

.method public static writeBytes(J[B)Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method
