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
    
    # Only scan rw- regions
    const-string v4, "rw-"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-nez v4, :check_anon
    goto :map_loop
    
    :check_anon
    # Skip .so files
    const-string v4, ".so"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :check_dev
    goto :map_loop
    
    :check_dev
    # Skip /dev/ regions
    const-string v4, "/dev/"
    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :parse_range
    goto :map_loop
    
    :parse_range
    invoke-static {v3}, Lcom/spy/MemoryMap;->parseAddressRange(Ljava/lang/String;)[J
    move-result-object v3
    
    const/4 v4, 0x0
    aget-wide v5, v3, v4
    const/4 v4, 0x1
    aget-wide v7, v3, v4
    
    # Calculate size
    sub-long v9, v7, v5
    
    # Skip if > 1MB (0x100000)
    const-wide/32 v3, 0x100000
    cmp-long v4, v9, v3
    if-lez v4, :scan_loop
    goto :map_loop
    
    :scan_loop
    # Result limit check
    invoke-interface {v0}, Ljava/util/List;->size()I
    move-result v4
    const/16 v9, 0x64
    if-le v4, v9, :size_check
    goto :scan_done
    
    :size_check
    # Overall limit - max 1 million addresses checked
    const v9, 0xf4240
    if-le v12, v9, :continue_scan
    goto :scan_done
    
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
    
    # Increment counter every 1024 checks
    add-int/lit8 v11, v11, 0x1
    rem-int/lit16 v4, v11, 0x400
    if-nez v4, :scan_loop
    add-int/lit16 v12, v12, 0x400
    goto :scan_loop
    
    :scan_done
    return-object v0
.end method
