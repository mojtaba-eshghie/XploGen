; ModuleID = "SimpleAuction"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"

@"arithmetic_result" = global i256 0
@"msg_sender_balance" = global i256 0
@"msg_value" = global i256 0
define i256 @"call.value"() 
{
entry:
  ret i256 0
}

define i256 @"call.gas"() 
{
entry:
  ret i256 0
}

@"global_SimpleAuction_beneficiary" = global i160 1
@"global_SimpleAuction_auctionEnd" = global i256 1
@"global_SimpleAuction_highestBidder" = global i160 1
@"global_SimpleAuction_highestBid" = global i256 1
@"global_SimpleAuction_pendingReturns" = external global i256
@"global_SimpleAuction_accounts" = external global i160
@"global_SimpleAuction_ended" = global i1 1
@"global_SimpleAuction_haha" = external global {i160, i256}
@"global_SimpleAuction_someData" = external global i256
define i256 @"SimpleAuction_Func_HighestBidIncreased972733"(i160 %".1", i256 %".2") 
{
entry:
  %"funcArg_SimpleAuction_Func_HighestBidIncreased972733_bidder" = alloca i160
  store i160 %".1", i160* %"funcArg_SimpleAuction_Func_HighestBidIncreased972733_bidder"
  %"funcArg_SimpleAuction_Func_HighestBidIncreased972733_amount" = alloca i256
  store i256 %".2", i256* %"funcArg_SimpleAuction_Func_HighestBidIncreased972733_amount"
  ret i256 0
}

define i256 @"SimpleAuction_Func_AuctionEnded972733"(i160 %".1", i256 %".2") 
{
entry:
  %"funcArg_SimpleAuction_Func_AuctionEnded972733_winner" = alloca i160
  store i160 %".1", i160* %"funcArg_SimpleAuction_Func_AuctionEnded972733_winner"
  %"funcArg_SimpleAuction_Func_AuctionEnded972733_amount" = alloca i256
  store i256 %".2", i256* %"funcArg_SimpleAuction_Func_AuctionEnded972733_amount"
  ret i256 0
}

define i256 @"SimpleAuction_Constructor"(i256 %".1", i160 %".2") 
{
entry:
  %"funcArg_SimpleAuction_Constructor__biddingTime" = alloca i256
  store i256 %".1", i256* %"funcArg_SimpleAuction_Constructor__biddingTime"
  %"funcArg_SimpleAuction_Constructor__beneficiary" = alloca i160
  store i160 %".2", i160* %"funcArg_SimpleAuction_Constructor__beneficiary"
  %"funcArg_SimpleAuction_Constructor_retParam" = alloca i256
  %"leftOpValue" = load i160, i160* @"global_SimpleAuction_beneficiary"
  %"rightOpValue" = load i160, i160* %"funcArg_SimpleAuction_Constructor__beneficiary"
  store i160 %"rightOpValue", i160* @"global_SimpleAuction_beneficiary"
  %"now" = alloca i256
  store i256 1722773259, i256* %"now"
  %"now.1" = load i256, i256* %"now"
  %"rightOpValue.1" = load i256, i256* %"funcArg_SimpleAuction_Constructor__biddingTime"
  %"intAdd" = add i256 %"now.1", %"rightOpValue.1"
  %"leftOpValue.1" = load i256, i256* @"global_SimpleAuction_auctionEnd"
  store i256 %"intAdd", i256* @"global_SimpleAuction_auctionEnd"
  ret i256 0
}

define i256 @"SimpleAuction_Func_function(uinta,uintb)public{}676966"(i256 %".1", i256 %".2") 
{
entry:
  %"funcArg_SimpleAuction_Func_function(uinta,uintb)public{}676966_a" = alloca i256
  store i256 %".1", i256* %"funcArg_SimpleAuction_Func_function(uinta,uintb)public{}676966_a"
  %"funcArg_SimpleAuction_Func_function(uinta,uintb)public{}676966_b" = alloca i256
  store i256 %".2", i256* %"funcArg_SimpleAuction_Func_function(uinta,uintb)public{}676966_b"
  %"funcArg_SimpleAuction_Func_function(uinta,uintb)public{}676966_retParam" = alloca i256
  ret i256 0
}

define i256 @"SimpleAuction_Func_function(SimpleAuctiona)public{}694335"(i256 %".1") 
{
entry:
  %"funcArg_SimpleAuction_Func_function(SimpleAuctiona)public{}694335_a" = alloca i256
  store i256 %".1", i256* %"funcArg_SimpleAuction_Func_function(SimpleAuctiona)public{}694335_a"
  %"funcArg_SimpleAuction_Func_function(SimpleAuctiona)public{}694335_retParam" = alloca i256
  ret i256 0
}

define i256 @"SimpleAuction_Func_bid270883"() 
{
entry:
  %"funcArg_SimpleAuction_Func_bid270883_retParam" = alloca i256
  %"now" = alloca i256
  br label %"requireStart"
requireStart:
  store i256 1722773259, i256* %"now"
  %"now.1" = load i256, i256* %"now"
  %"rightOpValue" = load i256, i256* @"global_SimpleAuction_auctionEnd"
  %"cmpOP" = icmp ule i256 %"now.1", %"rightOpValue"
  %"zextInst" = zext i1 %"cmpOP" to i256
  %"notNull" = icmp ne i256 %"zextInst", 0
  br i1 %"notNull", label %"endRequire", label %"sanityCheckUnsatisfied"
sanityCheckUnsatisfied:
  ret i256 -1
endRequire:
  br label %"requireStart.1"
requireStart.1:
  %"leftOpValue" = load i256, i256* @"msg_value"
  %"rightOpValue.1" = load i256, i256* @"global_SimpleAuction_highestBid"
  %"cmpOP.1" = icmp ugt i256 %"leftOpValue", %"rightOpValue.1"
  %"zextInst.1" = zext i1 %"cmpOP.1" to i256
  %"notNull.1" = icmp ne i256 %"zextInst.1", 0
  br i1 %"notNull.1", label %"endRequire.1", label %"sanityCheckUnsatisfied.1"
sanityCheckUnsatisfied.1:
  ret i256 -1
endRequire.1:
  br label %"ifStart"
ifStart:
  %"leftOpValue.1" = load i256, i256* @"global_SimpleAuction_highestBid"
  %"cmpOP.2" = icmp ne i256 %"leftOpValue.1", 0
  %"zextInst.2" = zext i1 %"cmpOP.2" to i256
  %"notNull.2" = icmp ne i256 %"zextInst.2", 0
  br i1 %"notNull.2", label %"then", label %"endIf"
then:
  %"leftOpValue.2" = load i256, i256* @"global_SimpleAuction_pendingReturns"
  %"rightOpValue.2" = load i256, i256* @"global_SimpleAuction_highestBid"
  %"assign_value" = add i256 %"leftOpValue.2", %"rightOpValue.2"
  store i256 %"assign_value", i256* @"global_SimpleAuction_pendingReturns"
  br label %"endIf"
endIf:
  %"leftOpValue.3" = load i160, i160* @"global_SimpleAuction_highestBidder"
  store i160 0, i160* @"global_SimpleAuction_highestBidder"
  %"leftOpValue.4" = load i256, i256* @"global_SimpleAuction_highestBid"
  %"rightOpValue.3" = load i256, i256* @"msg_value"
  store i256 %"rightOpValue.3", i256* @"global_SimpleAuction_highestBid"
  %"callArgValue" = load i256, i256* @"msg_value"
  %"FunctionCall" = call i256 @"SimpleAuction_Func_HighestBidIncreased972733"(i160 0, i256 %"callArgValue")
  ret i256 %"FunctionCall"
}

define i1 @"SimpleAuction_Func_withdraw270883"() 
{
entry:
  %"funcArg_SimpleAuction_Func_withdraw270883_retParam" = alloca i1
  %"initialValue" = load i256, i256* @"global_SimpleAuction_pendingReturns"
  %"funcArg_SimpleAuction_Func_withdraw270883_amount" = alloca i256
  store i256 %"initialValue", i256* %"funcArg_SimpleAuction_Func_withdraw270883_amount"
  br label %"ifStart"
ifStart:
  %"leftOpValue" = load i256, i256* %"funcArg_SimpleAuction_Func_withdraw270883_amount"
  %"cmpOP" = icmp ugt i256 %"leftOpValue", 0
  %"zextInst" = zext i1 %"cmpOP" to i256
  %"notNull" = icmp ne i256 %"zextInst", 0
  br i1 %"notNull", label %"then", label %"endIf"
then:
  %"leftOpValue.1" = load i256, i256* @"global_SimpleAuction_pendingReturns"
  store i256 0, i256* @"global_SimpleAuction_pendingReturns"
  br label %"ifStart.1"
ifStart.1:
  %"trxAmount" = load i256, i256* %"funcArg_SimpleAuction_Func_withdraw270883_amount"
  %"recvBalance" = load i256, i256* @"msg_sender_balance"
  %"sendingBalance" = add i256 %"recvBalance", %"trxAmount"
  store i256 %"sendingBalance", i256* @"msg_sender_balance"
  %"unaryBitNeg" = sub i256 0, 1
  %"notNull.1" = icmp ne i256 %"unaryBitNeg", 0
  br i1 %"notNull.1", label %"then.1", label %"endIf.1"
then.1:
  %"leftOpValue.2" = load i256, i256* @"global_SimpleAuction_pendingReturns"
  %"rightOpValue" = load i256, i256* %"funcArg_SimpleAuction_Func_withdraw270883_amount"
  store i256 %"rightOpValue", i256* @"global_SimpleAuction_pendingReturns"
  br label %"endIf.1"
endIf.1:
  br label %"endIf"
endIf:
  ret i1 1
}

define i256 @"SimpleAuction_Func_lol270883"() 
{
entry:
  %"funcArg_SimpleAuction_Func_lol270883_retParam" = alloca i256
  %"funcRetValue" = load i256, i256* @"global_SimpleAuction_pendingReturns"
  ret i256 %"funcRetValue"
}

define i256 @"SimpleAuction_Func_auctionEnd270883"() 
{
entry:
  %"funcArg_SimpleAuction_Func_auctionEnd270883_retParam" = alloca i256
  %"now" = alloca i256
  br label %"requireStart"
requireStart:
  store i256 1722773259, i256* %"now"
  %"now.1" = load i256, i256* %"now"
  %"rightOpValue" = load i256, i256* @"global_SimpleAuction_auctionEnd"
  %"cmpOP" = icmp uge i256 %"now.1", %"rightOpValue"
  %"zextInst" = zext i1 %"cmpOP" to i256
  %"notNull" = icmp ne i256 %"zextInst", 0
  br i1 %"notNull", label %"endRequire", label %"sanityCheckUnsatisfied"
sanityCheckUnsatisfied:
  ret i256 -1
endRequire:
  br label %"requireStart.1"
requireStart.1:
  %"unaryOpValue" = load i1, i1* @"global_SimpleAuction_ended"
  %"unaryBitNeg" = sub i1 0, %"unaryOpValue"
  %"notNull.1" = icmp ne i1 %"unaryBitNeg", 0
  br i1 %"notNull.1", label %"endRequire.1", label %"sanityCheckUnsatisfied.1"
sanityCheckUnsatisfied.1:
  ret i256 -1
endRequire.1:
  %"leftOpValue" = load i1, i1* @"global_SimpleAuction_ended"
  store i1 1, i1* @"global_SimpleAuction_ended"
  %"callArgValue" = load i160, i160* @"global_SimpleAuction_highestBidder"
  %"callArgValue.1" = load i256, i256* @"global_SimpleAuction_highestBid"
  %"FunctionCall" = call i256 @"SimpleAuction_Func_AuctionEnded972733"(i160 %"callArgValue", i256 %"callArgValue.1")
  ret i256 0
}
