.class public Lcom/spy/MemoryScanner;
.super Ljava/lang/Object;

.method public static scanInt(I)Ljava/util/List;
    .locals 13

    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    invoke-static {}, Lcom/spy/MemoryMap;->getMaps()Ljava/util/List;
    move-result-object v1

    invoke-interface {v1}, Ljava/util/List;->iterator()Ljava/util/Iterator;
    move-result-object v2

    const/4 v11, 0x0
    const/4 v12, 0x0

    :map_loop
    invoke-interface {v2}, Ljava/util/Iterator;->hasNext()Z
    move-result v3
    if-nez v3, :continue_map
    goto :scan_done

    :continue_map
    invoke-interface {v2}, Ljava/util/Iterator;->next()Ljava/lang/Object;
    move-result-object v3
    check-cast v3, Ljava/lang/String;

    # Accept rw- or r-- (scan data memory)
    const-string v4, "rw-"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :check_readonly
    goto :parse_range

    :check_readonly
    const-string v4, "r--"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-nez v4, :parse_range
    goto :map_loop

    :parse_range
    invoke-static {v3}, Lcom/spy/MemoryMap;->parseAddressRange(Ljava/lang/String;)[J
    move-result-object v3

    const/4 v4, 0x0
    aget-wide v5, v3, v4
    const/4 v4, 0x1
    aget-wide v7, v3, v4

    sub-long v9, v7, v5

    # FINAL: 32MB max per region (large game regions)
    const-wide/32 v3, 0x2000000
    cmp-long v4, v9, v3
    if-lez v4, :scan_loop
    goto :map_loop

    :scan_loop
    # FINAL: 50,000 max results (massive coverage)
    invoke-interface {v0}, Ljava/util/List;->size()I
    move-result v4
    const v9, 0xC350
    if-le v4, v9, :size_check
    goto :scan_done

    :size_check
    # FINAL: NO TOTAL LIMIT - Scan entire memory until 50k results
    # Removed the total scan limit check completely

    :continue_scan
    cmp-long v4, v5, v7
    if-gez v4, :map_loop

    :try_start
    invoke-static {v5, v6}, Lcom/spy/MemoryReader;->readInt(J)I
    move-result v10

    if-ne v10, p0, :next_addr

    invoke-static {v5, v6}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;
    move-result-object v4
    invoke-interface {v0, v4}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :next_addr

    :next_addr
    const-wide/16 v3, 0x4
    add-long/2addr v5, v3

    add-int/lit8 v11, v11, 0x1
    goto :scan_loop

    :scan_done
    return-object v0
.end method

.method public static scanHex(Ljava/lang/String;)Ljava/util/List;
    .locals 17

    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    invoke-static/range {p0 .. p0}, Lcom/spy/MemorySpy;->hexToBytes(Ljava/lang/String;)[B
    move-result-object v14

    array-length v15, v14
    if-nez v15, :continue_scan
    return-object v0

    :continue_scan
    invoke-static {}, Lcom/spy/MemoryMap;->getMaps()Ljava/util/List;
    move-result-object v1

    invoke-interface {v1}, Ljava/util/List;->iterator()Ljava/util/Iterator;
    move-result-object v2

    const/4 v11, 0x0
    const/4 v12, 0x0

    :map_loop
    invoke-interface {v2}, Ljava/util/Iterator;->hasNext()Z
    move-result v3
    if-nez v3, :continue_map
    goto :scan_done

    :continue_map
    invoke-interface {v2}, Ljava/util/Iterator;->next()Ljava/lang/Object;
    move-result-object v3
    check-cast v3, Ljava/lang/String;

    # Accept rw- or r--
    const-string v4, "rw-"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :check_readonly
    goto :parse_range

    :check_readonly
    const-string v4, "r--"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-nez v4, :parse_range
    goto :map_loop

    :parse_range
    invoke-static {v3}, Lcom/spy/MemoryMap;->parseAddressRange(Ljava/lang/String;)[J
    move-result-object v3

    const/4 v4, 0x0
    aget-wide v5, v3, v4
    const/4 v4, 0x1
    aget-wide v7, v3, v4

    sub-long v9, v7, v5

    # FINAL: 32MB max per region
    const-wide/32 v3, 0x2000000
    cmp-long v4, v9, v3
    if-lez v4, :scan_loop
    goto :map_loop

    :scan_loop
    # FINAL: 50,000 max results
    invoke-interface {v0}, Ljava/util/List;->size()I
    move-result v4
    const v9, 0xC350
    if-le v4, v9, :size_check
    goto :scan_done

    :size_check
    # FINAL: NO TOTAL LIMIT - Scan everything

    :continue_inner
    cmp-long v4, v5, v7
    if-gez v4, :map_loop

    :try_start
    move v13, v15
    invoke-static {v5, v6, v13}, Lcom/spy/MemoryReader;->readBytes(JI)[B
    move-result-object v10

    array-length v4, v10
    if-ge v4, v15, :compare_bytes
    goto :next_addr

    :compare_bytes
    const/4 v4, 0x1
    const/4 v9, 0x0

    :byte_loop
    if-ge v9, v15, :check_match

    aget-byte v13, v10, v9
    aget-byte v16, v14, v9
    move/from16 v3, v16
    if-eq v13, v3, :next_byte
    const/4 v4, 0x0
    goto :next_addr

    :next_byte
    add-int/lit8 v9, v9, 0x1
    goto :byte_loop

    :check_match
    if-nez v4, :next_addr

    invoke-static {v5, v6}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;
    move-result-object v4
    invoke-interface {v0, v4}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :next_addr

    :next_addr
    const-wide/16 v3, 0x1
    add-long/2addr v5, v3

    add-int/lit8 v11, v11, 0x1
    goto :scan_loop

    :scan_done
    return-object v0
.end method
