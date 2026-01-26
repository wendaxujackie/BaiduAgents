@echo off
chcp 65001 >nul
title APK随机关键词副本生成工具 V3.1
color 0A
setlocal enabledelayedexpansion

echo ============================================
echo   APK随机关键词副本批量生成工具 - 完全随机版
echo ============================================
echo.

REM 保存当前目录路径
set "currentDir=%cd%"

REM 创建目标文件夹（如果不存在）
set "targetFolder=2026发发发"
if not exist "%targetFolder%" (
    mkdir "%targetFolder%"
    echo 创建目标文件夹: %targetFolder%
) else (
    echo 目标文件夹已存在: %targetFolder%
)
echo.

REM 定义关键词数组（10个关键词）
set "keywords[0]=官方版"
set "keywords[1]=手机版"
set "keywords[2]=最新版"
set "keywords[3]=中文版"
set "keywords[4]=手游"
set "keywords[5]=汉化版"
set "keywords[6]=官方正版"
set "keywords[7]=安卓版"
set "keywords[8]=手机版下载"
set "keywords[9]=安卓版下载"

REM 统计APK文件数量
set fileCount=0
for %%f in (*.apk) do set /a fileCount+=1

if %fileCount% equ 0 (
    echo 错误：当前目录中没有找到APK文件！
    echo 请将本脚本放在包含APK文件的目录中运行。
    echo.
    pause
    exit /b 1
)

echo 发现 %fileCount% 个APK文件
echo 将为每个APK文件创建7个完全随机的关键词副本
echo 所有文件将直接生成到"2026发发发"文件夹中
echo.

set totalCopies=0
set processedFiles=0

echo 正在初始化高级随机数生成器...
timeout /t 1 /nobreak >nul

REM 记录原始APK文件列表
set index=0
for %%f in (*.apk) do (
    set "originalFile[!index!]=%%f"
    set /a index+=1
)

set totalFiles=!index!

REM 为每个APK文件创建关键词副本
for /l %%i in (0,1,!totalFiles!) do (
    if defined originalFile[%%i] (
        call :processFile "!originalFile[%%i]!"
    )
)

goto :showSummary

:processFile
set "originalName=%~1"
set "filename=%~n1"
set "extension=%~x1"

echo.
echo ============================================
echo 正在处理第 !processedFiles!+1 个文件: !originalName!
echo ============================================

echo 正在生成7个完全不重复的随机关键词副本...

REM 创建Fisher-Yates洗牌算法的索引数组
for /l %%i in (0,1,9) do set "shuffle[%%i]=%%i"

REM 使用增强的随机性进行洗牌
for /l %%i in (9,-1,1) do (
    call :getEnhancedRandom %%i
    set /a j=!randNum!
    
    REM 交换位置
    set temp=!shuffle[%%i]!
    set shuffle[%%i]=!shuffle[!j!]!
    set shuffle[!j!]=!temp!
)

REM 使用洗牌后的前7个关键词创建副本
set copyCount=0
for /l %%k in (0,1,6) do (
    set /a idx=!shuffle[%%k]!
    
    REM 使用call来正确获取中文关键词
    call :getKeyword !idx!
    
    set "newName=!filename!!keyword!!extension!"
    
    REM 检查目标文件夹中是否已存在同名文件
    if not exist "%targetFolder%\!newName!" (
        REM 直接复制到目标文件夹
        copy /y "!originalName!" "%targetFolder%\!newName!" >nul 2>&1
        
        if !errorlevel! equ 0 (
            set /a copyCount+=1
            set /a totalCopies+=1
            echo 创建副本 !copyCount!: !newName!
        ) else (
            echo 警告: 创建副本失败 - !newName!
        )
    ) else (
        echo 跳过: !newName! 在目标文件夹中已存在
        REM 尝试使用备用关键词（使用洗牌数组中的下一个）
        for /l %%m in (7,1,9) do (
            if !copyCount! lss 7 (
                set /a altIdx=!shuffle[%%m]!
                call :getKeyword !altIdx!
                set "altName=!filename!!keyword!!extension!"
                
                if not exist "%targetFolder%\!altName!" (
                    copy /y "!originalName!" "%targetFolder%\!altName!" >nul 2>&1
                    if !errorlevel! equ 0 (
                        set /a copyCount+=1
                        set /a totalCopies+=1
                        echo 创建副本 !copyCount!（备用）: !altName!
                    )
                )
            )
        )
    )
)

echo 完成: 为 !originalName! 创建了 !copyCount! 个不重复的关键词副本
set /a processedFiles+=1

REM 清理临时数组
for /l %%i in (0,1,9) do set "shuffle[%%i]="
set "keyword="
set "newName="
goto :eof

:getKeyword
set "keywordIndex=%~1"
REM 使用临时变量存储索引值
set "tempIdx=!keywordIndex!"

REM 根据索引获取对应的中文关键词
if !tempIdx!==0 set "keyword=官方版" & goto :eof
if !tempIdx!==1 set "keyword=手机版" & goto :eof
if !tempIdx!==2 set "keyword=最新版" & goto :eof
if !tempIdx!==3 set "keyword=中文版" & goto :eof
if !tempIdx!==4 set "keyword=手游" & goto :eof
if !tempIdx!==5 set "keyword=汉化版" & goto :eof
if !tempIdx!==6 set "keyword=官方正版" & goto :eof
if !tempIdx!==7 set "keyword=安卓版" & goto :eof
if !tempIdx!==8 set "keyword=手机版下载" & goto :eof
if !tempIdx!==9 set "keyword=安卓版下载" & goto :eof
goto :eof

:getEnhancedRandom
set "maxVal=%~1"
REM 使用多种随机源组合
set /a r1=!random! %% (!maxVal! + 1)
set /a r2=!time:~-5,4! %% (!maxVal! + 1)
set /a r3=!processedFiles! %% (!maxVal! + 1)
set /a r4=!totalCopies! %% (!maxVal! + 1)
set /a r5=!filename:~0,1! 2>nul

REM 将字符转换为ASCII码值
for /f %%a in ('cmd /c "echo(!r5!"') do set /a r5=%%a 2>nul

set /a randNum=(r1 * r2 + r3 + r4 + r5) %% (!maxVal! + 1)
if !randNum! lss 0 set /a randNum=-randNum
goto :eof

:showSummary
echo.
echo ============================================
echo 正在移动原始APK文件到目标文件夹...
echo ============================================

REM 移动原始文件到目标文件夹
set originalMoved=0
for /l %%i in (0,1,!totalFiles!) do (
    if defined originalFile[%%i] (
        set "origFile=!originalFile[%%i]!"
        if exist "!origFile!" (
            move /y "!origFile!" "%targetFolder%\" >nul 2>&1
            if !errorlevel! equ 0 (
                set /a originalMoved+=1
            ) else (
                echo 警告: 移动原始文件失败 - !origFile!
            )
        )
    )
)

echo 已移动 !originalMoved! 个原始文件
echo.

echo ============================================
echo 生成完成！
echo ============================================
echo.
echo 统计信息:
echo ============================================
echo 处理的原始文件: %processedFiles% 个
echo 创建的关键词副本总数: %totalCopies% 个
echo.
echo 所有文件已保存到文件夹: %targetFolder%
echo 包含内容:
echo   - %processedFiles% 个原始APK文件
echo   - %totalCopies% 个关键词副本文件
echo   - 总共 %processedFiles%+%totalCopies% 个APK文件
echo.
echo 命名格式: 原文件名关键词.apk
echo 示例: 
echo   game手游.apk
echo   game汉化版.apk  
echo   game官方版.apk
echo   game最新版.apk
echo   game中文版.apk
echo   game安卓版.apk
echo   game手机版下载.apk
echo ============================================
echo.

REM 显示目标文件夹中的文件统计
if exist "%targetFolder%\" (
    pushd "%targetFolder%"
    set targetFileCount=0
    for %%f in (*.apk) do set /a targetFileCount+=1
    popd
    echo 目标文件夹中现有 !targetFileCount! 个APK文件
    echo.
)

echo 按任意键打开目标文件夹查看所有文件...感谢使用本工具，纯友情制作，且用且珍惜。
pause >nul

REM 打开目标文件夹
if exist "%currentDir%\%targetFolder%\" (
    explorer "%currentDir%\%targetFolder%"
)

echo.
echo 处理完成！所有APK文件已整理到"2026发发发"文件夹中。
echo 按任意键退出... 感谢使用本工具，纯友情制作，且用且珍惜。
pause >nul

endlocal
exit /b 0