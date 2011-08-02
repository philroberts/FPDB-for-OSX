//
//  tablemonitor.h
//  axlib
//
//  Created by Philip Roberts on 1/08/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import <Cocoa/Cocoa.h>


@interface tmcallback : NSObject
{
}

-(void)callback:(NSString*)tablename event:(NSString*)eventtype;

@end

@interface closedcallback : NSObject
{
	tmcallback **myCB;
	NSString *title;
}

@property (assign) tmcallback **myCB;
@property (copy) NSString *title;

-(void)sendCB;

@end


@interface tablemonitor : NSObject {
	tmcallback *myCB;
	__strong AXUIElementRef appRef;
	pid_t appPID;
	__strong AXObserverRef observer;
}

@property (assign) AXUIElementRef appRef;
@property (assign) pid_t appPID;
@property (assign) tmcallback *myCB;

-(void)detectFakePS;
-(void)registerCallback:(tmcallback*)cb;
-(void)runCallback;
-(void)runCallback:(NSString*)msg;
-(void)runCallback:(NSString*)table event:(NSString*)eventtype;
-(void)doObserver;
-(void)assignCCB:(closedcallback*)ccb;

@end
