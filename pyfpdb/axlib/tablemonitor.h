
#import <Cocoa/Cocoa.h>


@interface TMCallback : NSObject
{
}

-(void)callback:(NSString*)tablename event:(NSString*)eventtype;

@end

@interface ClosedCallback : NSObject
{
	TMCallback **myCB;
	NSString *title;
}

@property (assign) TMCallback **myCB;
@property (copy) NSString *title;

-(void)sendCB;

@end


@interface TableMonitor : NSObject {
	TMCallback *myCB;
	__strong AXUIElementRef appRef;
	pid_t appPID;
	__strong AXObserverRef observer;
}

@property (assign) AXUIElementRef appRef;
@property (assign) pid_t appPID;
@property (assign) TMCallback *myCB;

-(void)detectFakePS;
-(void)registerCallback:(TMCallback*)cb;
-(void)runCallback;
-(void)runCallback:(NSString*)msg;
-(void)runCallback:(NSString*)table event:(NSString*)eventtype;
-(void)doObserver;
-(void)assignCCB:(ClosedCallback*)ccb;

@end
