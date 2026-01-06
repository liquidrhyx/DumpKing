.class public Lcom/spy/MemoryMap;
.super Ljava/lang/Object;

.method public static getMaps()Ljava/util/List;
    .locals 5

    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    :try_start
    new-instance v1, Ljava/io/BufferedReader;
    new-instance v2, Ljava/io/FileReader;
    const-string v3, "/proc/self/maps"
    invoke-direct {v2, v3}, Ljava/io/FileReader;-><init>(Ljava/lang/String;)V
    invoke-direct {v1, v2}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    :read_loop
    invoke-virtual {v1}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v2
    if-nez v2, :add_line
    goto :done

    :add_line
    invoke-interface {v0, v2}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    goto :read_loop

    :done
    invoke-virtual {v1}, Ljava/io/BufferedReader;->close()V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all

    return-object v0

    :catch_all
    return-object v0
.end method

.method public static parseAddressRange(Ljava/lang/String;)[J
    .locals 6

    const/4 v0, 0x2
    new-array v1, v0, [J

    :try_start
    const-string v0, " "
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0

    const/4 v2, 0x0
    aget-object v0, v0, v2

    const-string v2, "-"
    invoke-virtual {v0, v2}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0

    const/4 v2, 0x0
    aget-object v3, v0, v2
    const/16 v4, 0x10
    invoke-static {v3, v4}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v3
    aput-wide v3, v1, v2

    const/4 v2, 0x1
    aget-object v3, v0, v2
    const/16 v4, 0x10
    invoke-static {v3, v4}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J
    move-result-wide v3
    aput-wide v3, v1, v2
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_all

    return-object v1

    :catch_all
    return-object v1
.end method
